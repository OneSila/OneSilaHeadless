from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager
from django.db.models import Subquery, OuterRef, Value, CharField
from django.db.models.functions import Coalesce


class ProductQuerySet(MultiTenantQuerySet):
    def filter_configurable(self):
        return self.filter(type=self.model.CONFIGURABLE)

    def filter_variation(self):
        return self.filter(type=self.model.SIMPLE)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)

    def filter_has_prices(self):
        return self.filter(type__in=self.model.HAS_PRICES_TYPES)

    def with_translated_name(self):
        from .models import ProductTranslation

        language_field = OuterRef('multi_tenant_company__language')
        name_in_language = ProductTranslation.objects.filter(
            product=OuterRef('pk'),
            language=language_field,
        ).values('name')[:1]

        any_name = ProductTranslation.objects.filter(
            product=OuterRef('pk'),
        ).values('name')[:1]

        return self.annotate(
            translated_name=Coalesce(
                Subquery(name_in_language, output_field=CharField()),
                Subquery(any_name, output_field=CharField()),
                Value('No Name Set'),
            )
        )

    def filter_by_properties_rule(self, rule):
        from properties.models import ProductProperty
        product_ids = ProductProperty.objects.filter(value_select=rule.product_type).values_list('product_id', flat=True)
        return self.filter_multi_tenant(multi_tenant_company=rule.multi_tenant_company).filter(id__in=product_ids)

    def filter_by_product_type(self, product_type):
        from properties.models import ProductProperty
        product_ids = ProductProperty.objects.filter(value_select=product_type).values_list('product_id', flat=True)
        return self.filter_multi_tenant(multi_tenant_company=product_type.multi_tenant_company).filter(id__in=product_ids)

    def duplicate_product(self, product, *, sku=None, create_as_alias=False):
        from django.db import transaction
        from django.core.exceptions import ValidationError
        from .models import (
            Product,
            ProductTranslation,
            ProductTranslationBulletPoint,
            ConfigurableVariation,
            BundleVariation,
        )
        from media.models import MediaProductThrough
        from properties.models import (
            ProductProperty,
            ProductPropertyTextTranslation,
        )
        from sales_prices.models import SalesPrice, SalesPriceListItem

        multi_tenant_company = product.multi_tenant_company

        if sku is not None and Product.objects.filter(
            multi_tenant_company=multi_tenant_company,
            sku=sku,
        ).exists():
            raise ValidationError("SKU already exists")

        if create_as_alias and product.is_configurable():
            raise ValidationError("Cannot create alias for configurable products")

        with transaction.atomic():
            new_product = Product.objects.create(
                multi_tenant_company=multi_tenant_company,
                sku=sku,
                active=product.active,
                type=Product.ALIAS if create_as_alias else product.type,
                vat_rate=product.vat_rate,
                allow_backorder=product.allow_backorder,
                alias_parent_product=product if create_as_alias else product.alias_parent_product,
                created_by_multi_tenant_user=product.created_by_multi_tenant_user,
                last_update_by_multi_tenant_user=product.last_update_by_multi_tenant_user,
            )

            # Translations
            for trans in product.translations.all():
                new_trans = ProductTranslation.objects.create(
                    product=new_product,
                    sales_channel=trans.sales_channel,
                    name=trans.name,
                    short_description=trans.short_description,
                    description=trans.description,
                    url_key=trans.url_key,
                    language=trans.language,
                    multi_tenant_company=multi_tenant_company,
                )
                for bp in trans.bullet_points.all():
                    ProductTranslationBulletPoint.objects.create(
                        multi_tenant_company=multi_tenant_company,
                        product_translation=new_trans,
                        text=bp.text,
                        sort_order=bp.sort_order,
                    )

            # Images
            MediaProductThrough.objects.bulk_create([
                MediaProductThrough(
                    media=img.media,
                    product=new_product,
                    sort_order=img.sort_order,
                    is_main_image=img.is_main_image,
                    multi_tenant_company=multi_tenant_company,
                )
                for img in MediaProductThrough.objects.filter(product=product)
            ])

            # Properties
            for pp in ProductProperty.objects.filter(product=product).select_related("property"):
                new_pp = ProductProperty.objects.create(
                    product=new_product,
                    property=pp.property,
                    value_boolean=pp.value_boolean,
                    value_int=pp.value_int,
                    value_float=pp.value_float,
                    value_date=pp.value_date,
                    value_datetime=pp.value_datetime,
                    value_select=pp.value_select,
                    multi_tenant_company=multi_tenant_company,
                )

                for t in pp.productpropertytexttranslation_set.all():
                    ProductPropertyTextTranslation.objects.create(
                        product_property=new_pp,
                        language=t.language,
                        value_text=t.value_text,
                        value_description=t.value_description,
                        multi_tenant_company=multi_tenant_company,
                    )

            # Prices
            for sp in SalesPrice.objects.filter(product=product):
                SalesPrice.objects.create(
                    product=new_product,
                    currency=sp.currency,
                    rrp=sp.rrp,
                    price=sp.price,
                    multi_tenant_company=multi_tenant_company,
                )

            for item in SalesPriceListItem.objects.filter(product=product):
                SalesPriceListItem.objects.create(
                    salespricelist=item.salespricelist,
                    product=new_product,
                    price_auto=item.price_auto,
                    discount_auto=item.discount_auto,
                    price_override=item.price_override,
                    discount_override=item.discount_override,
                    multi_tenant_company=multi_tenant_company,
                )

            # Configurable variations
            for cv in ConfigurableVariation.objects.filter(parent=product):
                ConfigurableVariation.objects.create(
                    parent=new_product,
                    variation=cv.variation,
                    multi_tenant_company=multi_tenant_company,
                )

            for cv in ConfigurableVariation.objects.filter(variation=product):
                ConfigurableVariation.objects.create(
                    parent=cv.parent,
                    variation=new_product,
                    multi_tenant_company=multi_tenant_company,
                )

            # Bundle variations
            for bv in BundleVariation.objects.filter(parent=product):
                BundleVariation.objects.create(
                    parent=new_product,
                    variation=bv.variation,
                    quantity=bv.quantity,
                    multi_tenant_company=multi_tenant_company,
                )

            for bv in BundleVariation.objects.filter(variation=product):
                BundleVariation.objects.create(
                    parent=bv.parent,
                    variation=new_product,
                    quantity=bv.quantity,
                    multi_tenant_company=multi_tenant_company,
                )

            return new_product


class ProductManager(MultiTenantManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def filter_by_properties_rule(self, rule):
        return self.get_queryset().filter_by_properties_rule(rule)

    def filter_by_product_type(self, product_type):
        return self.get_queryset().filter_by_product_type(product_type)

    def duplicate_product(self, product, **kwargs):
        return self.get_queryset().duplicate_product(product, **kwargs)


class ConfigurableQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class ConfigurableManager(ProductManager):
    def get_queryset(self):
        return ConfigurableQuerySet(self.model, using=self._db)


class VariationQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class VariationManager(ProductManager):
    def get_queryset(self):
        return VariationQuerySet(self.model, using=self._db)


class AliasProductQuerySet(QuerySetProxyModelMixin, ProductQuerySet):

    def copy_from_parent(self, alias_product, *, copy_images=False, copy_properties=False):
        from media.models import MediaProductThrough
        from properties.models import ProductProperty, Property, ProductPropertyTextTranslation

        parent = alias_product.alias_parent_product
        if not parent:
            raise ValueError("Alias product must have an alias_parent_product set.")

        if copy_images:
            parent_images = parent.mediaproductthrough_set.all()
            MediaProductThrough.objects.bulk_create([
                MediaProductThrough(
                    media=img.media,
                    product=alias_product,
                    sort_order=img.sort_order,
                    is_main_image=img.is_main_image,
                    multi_tenant_company=parent.multi_tenant_company
                ) for img in parent_images
            ])

        if copy_properties:
            parent_props = ProductProperty.objects.filter(product=parent).select_related('property')
            for pp in parent_props:
                new_pp = ProductProperty.objects.create(
                    product=alias_product,
                    property=pp.property,
                    value_boolean=pp.value_boolean,
                    value_int=pp.value_int,
                    value_float=pp.value_float,
                    value_date=pp.value_date,
                    value_datetime=pp.value_datetime,
                    value_select=pp.value_select,
                    multi_tenant_company=parent.multi_tenant_company
                )

                if pp.property.type in Property.TYPES.TRANSLATED:
                    text_translations = ProductPropertyTextTranslation.objects.filter(product_property=pp)
                    for trans in text_translations:
                        ProductPropertyTextTranslation.objects.create(
                            product_property=new_pp,
                            language=trans.language,
                            value_text=trans.value_text,
                            value_description=trans.value_description,
                            multi_tenant_company=parent.multi_tenant_company
                        )


class AliasProductManager(ProductManager):

    def get_queryset(self):
        return AliasProductQuerySet(self.model, using=self._db)

    def copy_from_parent(self, alias_product, **kwargs):
        return self.get_queryset().copy_from_parent(alias_product, **kwargs)


class BundleQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    def get_all_item_products(self, product):
        from .models import Product, BundleVariation

        """
        Recursively fetch all products that are part of the BOM of the given manufacturable product.
        Returns a QuerySet of all BOM components.
        """

        def fetch_items_components(product, collected_ids=None):
            if collected_ids is None:
                collected_ids = set()

            # Get direct BundleVariation components
            direct_components = BundleVariation.objects.filter(parent=product).values_list('variation_id', flat=True)
            new_ids = set(direct_components) - collected_ids

            if not new_ids:
                return collected_ids

            collected_ids.update(new_ids)

            for variation in Product.objects.filter(id__in=new_ids).iterator():
                if variation.is_bundle():
                    fetch_items_components(variation, collected_ids)

            return collected_ids

        # Fetch all components
        all_items_component_ids = fetch_items_components(product)

        # Return a QuerySet of all the components
        return Product.objects.filter(id__in=all_items_component_ids)


class BundleManager(ProductManager):
    def get_queryset(self):
        return BundleQuerySet(self.model, using=self._db)

    def get_all_item_products(self, product):
        return self.get_queryset().get_all_item_products(product)
