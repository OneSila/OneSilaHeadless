from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager


class ProductQuerySet(MultiTenantQuerySet):
    def filter_configurable(self):
        return self.filter(type=self.model.CONFIGURABLE)

    def filter_variation(self):
        return self.filter(type=self.model.SIMPLE)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)

    def filter_has_prices(self):
        return self.filter(type__in=self.model.HAS_PRICES_TYPES)

    def filter_by_properties_rule(self, rule):
        from properties.models import ProductProperty
        product_ids = ProductProperty.objects.filter(value_select=rule.product_type).values_list('product_id', flat=True)
        return self.filter_multi_tenant(multi_tenant_company=rule.multi_tenant_company).filter(id__in=product_ids)

    def filter_by_product_type(self, product_type):
        from properties.models import ProductProperty
        product_ids = ProductProperty.objects.filter(value_select=product_type).values_list('product_id', flat=True)
        return self.filter_multi_tenant(multi_tenant_company=product_type.multi_tenant_company).filter(id__in=product_ids)

class ProductManager(MultiTenantManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def filter_by_properties_rule(self, rule):
        return self.get_queryset().filter_by_properties_rule(rule)

    def filter_by_product_type(self, product_type):
        return self.get_queryset().filter_by_product_type(product_type)


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
    pass


class AliasProductManager(ProductManager):
    def get_queryset(self):

        return AliasProductQuerySet(self.model, using=self._db)

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