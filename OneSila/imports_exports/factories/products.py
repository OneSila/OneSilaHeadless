from decimal import Decimal, InvalidOperation
from hashlib import shake_256

import shortuuid
from django.db import IntegrityError

from currencies.models import Currency, PublicCurrency
from eancodes.models import EanCode
from imports_exports.factories.media import ImportImageInstance
from imports_exports.factories.mixins import AbstractImportInstance, ImportOperationMixin
from imports_exports.factories.properties import ImportProductPropertiesRuleInstance, ImportProductPropertyInstance
from media.models import Image, MediaProductThrough
from products.models import (
    Product,
    ProductTranslation,
    ProductTranslationBulletPoint,
    ConfigurableVariation,
    BundleVariation,
)
from properties.models import Property, ProductPropertiesRuleItem, ProductProperty
from sales_prices.models import SalesPrice
from taxes.models import VatRate


class ProductImport(ImportOperationMixin):
    get_identifiers = ['sku', 'type']

    def resolve_get_or_create_integrity_error(self, error):
        sku = getattr(self.import_instance, 'sku', None)

        if not sku:
            raise error

        error_msg = str(error)
        is_duplicate_sku_constraint = (
                'duplicate key value violates unique constraint' in error_msg and
                'products_product_sku_multi_tenant_company_id' in error_msg
        )

        if not is_duplicate_sku_constraint:
            raise error

        existing = Product.objects.filter(sku=sku, multi_tenant_company=self.multi_tenant_company).first()

        if existing:
            self.created = False
            return existing, False

        raise error


class AliasProductImport(ImportOperationMixin):
    get_identifiers = ['sku', 'type', 'alias_parent_product']


class ProductTranslationImport(ImportOperationMixin):
    get_identifiers = ['product', 'language', 'sales_channel']


class SalesPriceImport(ImportOperationMixin):
    get_identifiers = ['product', 'currency']


class ImportProductInstance(AbstractImportInstance):

    def __init__(self, data: dict, import_process=None, rule=None, translations=None, instance=None, sales_channel=None, update_current_rule=False):
        super().__init__(data, import_process, instance)

        if translations is None:
            translations = []

        self.rule = rule
        self.translations = translations
        self.sales_channel = sales_channel
        self.update_current_rule = update_current_rule

        default_sku = shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(7)
        self.set_field_if_exists('name')
        self.set_field_if_exists('sku', default_sku)
        self.set_field_if_exists('type', default_value=Product.SIMPLE)

        self.set_field_if_exists('active')
        self.set_field_if_exists('vat_rate')
        self.set_field_if_exists('use_vat_rate_name')
        self.set_field_if_exists('ean_code')
        self.set_field_if_exists('allow_backorder')
        self.set_field_if_exists('alias_parent_product')

        # it's the rule
        self.set_field_if_exists('product_type')
        self.set_field_if_exists('properties')

        self.set_field_if_exists('translations')

        self.set_field_if_exists('images')
        self.set_field_if_exists('prices')

        self.set_field_if_exists('variations')
        self.set_field_if_exists('bundle_variations')
        self.set_field_if_exists('alias_variations')
        self.set_field_if_exists('configurator_select_values')

        # used to help remote imports
        self.set_field_if_exists('__image_index_to_remote_id')
        self.set_field_if_exists('__mirror_product_properties_map')
        self.set_field_if_exists('__variation_sku_to_id_map')

        if self.type == Product.ALIAS and not hasattr(self, 'alias_parent_product'):
            alias_sku = self.data.get('alias_parent_sku')
            if alias_sku:
                alias_parent_product = Product.objects.filter(
                    sku=alias_sku,
                    multi_tenant_company=self.multi_tenant_company
                ).first()

                if alias_parent_product:
                    self.alias_parent_product = alias_parent_product

        self.validate()

        self.created = False

        # Track created instances (initialized for safety and predictability)
        self.vat_rate_instance = None
        self.ean_code_instance = None
        self.rule_instance = None

        self.product_property_instances = ProductProperty.objects.none()
        self.translation_instances = ProductTranslation.objects.none()
        self.image_instances = Image.objects.none()
        self.images_associations_instances = MediaProductThrough.objects.none()
        self.variations_products_instances = Product.objects.none()
        self.bundle_variations_instances = Product.objects.none()
        self.alias_variations_instances = Product.objects.none()

    @property
    def local_class(self):
        return Product

    @property
    def updatable_fields(self):
        return ['active', 'allow_backorder', 'vat_rate']

    def validate(self):
        """
        Validate that the 'value' key exists.
        """
        if not hasattr(self, 'name'):
            raise ValueError("The 'name' field is required.")

        if hasattr(self, 'type') and self.type not in [Product.SIMPLE, Product.CONFIGURABLE, Product.BUNDLE, Product.ALIAS]:
            raise ValueError("Invalid 'type' value.")

    def _set_vat_rate(self):

        if hasattr(self, 'vat_rate'):

            if self.vat_rate is None:
                # that means that the values is None so we should set it as None
                return

            get_or_create_kwargs = {
                'multi_tenant_company': self.multi_tenant_company
            }

            if getattr(self, 'use_vat_rate_name', False):
                get_or_create_kwargs['name'] = self.vat_rate
            else:
                if isinstance(self.vat_rate, str):
                    self.vat_rate = int(self.vat_rate)

                get_or_create_kwargs['rate'] = self.vat_rate

            vat_rate_object, _ = VatRate.objects.get_or_create(**get_or_create_kwargs)

            self.vat_rate = vat_rate_object
            self.vat_rate_instance = self.vat_rate

    def update_ean_code(self):

        if not hasattr(self, 'ean_code') or not self.ean_code:
            return

        # Try to find by product first (for update case)
        self.ean_code_instance = EanCode.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product=self.instance,
        ).first()

        if self.ean_code_instance:
            # Product match found, but maybe EAN changed
            if self.ean_code_instance.ean_code != self.ean_code:
                self.ean_code_instance.ean_code = self.ean_code
        else:
            # Try to find an existing ean_code assigned elsewhere or unassigned
            existing_ean = EanCode.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                ean_code=self.ean_code,
            ).first()

            if existing_ean:
                # Reassign to the correct product
                self.ean_code_instance = existing_ean
                self.ean_code_instance.product = self.instance
            else:
                # Create new
                self.ean_code_instance = EanCode.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product=self.instance,
                    ean_code=self.ean_code,
                )

        # Common fields
        self.ean_code_instance.already_used = True
        self.ean_code_instance.internal = False
        self.ean_code_instance.save()

    def _set_rule(self):

        if self.rule and self.update_current_rule:
            self.update_product_rule()

        if not self.rule and not hasattr(self, 'product_type'):
            return

        required_names = set()
        if hasattr(self, 'configurator_select_values'):
            for select_value in self.configurator_select_values:
                if 'property_data' in select_value:
                    prop_data = select_value['property_data']
                    name = prop_data.get("name")
                    required_names.add(name)

                if "property" in select_value:
                    prop = select_value["property"]
                    required_names.add(prop.name)


        items = []
        if hasattr(self, 'properties'):
            for property in self.properties:
                if 'property_data' in property or 'property' in property:
                    if 'property_data' in property:
                        name = property['property_data'].get("name")
                        type = property['property_data'].get("type")

                        if type != Property.TYPES.SELECT:
                            continue

                        item_data = {
                            'property_data': property['property_data'],
                            'type': ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR if name in required_names else ProductPropertiesRuleItem.OPTIONAL
                        }
                    else:
                        name = property['property'].name
                        type = property['property'].type

                        if type != Property.TYPES.SELECT:
                            continue

                        item_data = {
                            'property': property['property'],
                            'type': ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR if name in required_names else ProductPropertiesRuleItem.OPTIONAL
                        }

                    items.append(item_data)

        if hasattr(self, 'product_type'):
            rule_import_instance = ImportProductPropertiesRuleInstance({"value": self.product_type, "items": items}, self.import_process)
            rule_import_instance.process()
            self.rule = rule_import_instance.instance
        else:
            rule_import_instance = ImportProductPropertiesRuleInstance({"items": items}, self.import_process, instance=self.rule)
            rule_import_instance.process()

        self.rule_instance = self.rule

    def _set_translations(self):

        if not getattr(self, 'translations', []):

            self.translations = [{
                'name': getattr(self, 'name', 'Unnamed'),
                'language': self.language,
                'sales_channel': self.sales_channel,
            }]

    def pre_process_logic(self):
        self._set_vat_rate()
        self._set_rule()
        self._set_translations()

    def process_logic(self):

        if self.type == Product.ALIAS:
            fac = AliasProductImport(self, self.import_process, instance=self.instance)
        else:
            fac = ProductImport(self, self.import_process, instance=self.instance)

        fac.run()

        # Save the created/updated instance.
        self.instance = fac.instance
        self.created = fac.created

        if self.created:
            self.create_translations()

    def update_product_rule(self):

        if self.rule and self.instance and self.rule != self.instance.get_product_rule():
            product_type_property = Property.objects.get(
                multi_tenant_company=self.multi_tenant_company,
                is_product_type=True
            )

            value_data = {
                'value': self.rule.product_type.id,
                'value_is_id': True
            }

            product_property_import_instance = ImportProductPropertyInstance(
                value_data,
                self.import_process,
                product=self.instance,
                property=product_type_property
            )

            product_property_import_instance.language = self.language
            product_property_import_instance.process()

    def set_product_properties(self):

        if self.created:
            self.update_product_rule()
        else:
            if self.update_current_rule:
                self.update_product_rule()


        product_property_ids = []
        if self.type in [Product.SIMPLE, Product.BUNDLE, Product.ALIAS] and hasattr(self, 'properties'):

            for property in self.properties:
                try:
                    property_instance = property.get('property', None)
                    product_property_import_instance = ImportProductPropertyInstance(
                        property,
                        self.import_process,
                        property=property_instance,
                        product=self.instance)

                    product_property_import_instance.language = self.language
                    product_property_import_instance.process()
                    product_property_ids.append(product_property_import_instance.instance.id)
                except Exception as e:
                    # @TODO: Come hare later and remove this except
                    pass

        self.product_property_instances = ProductProperty.objects.filter(id__in=product_property_ids)

    def set_images(self):

        images_instances_ids = []
        images_instances_associations_ids = []
        for image in self.images:

            image_import_instance = ImportImageInstance(
                image,
                import_process=self.import_process,
                product=self.instance
            )
            image_import_instance.process()

            if image_import_instance.instance is not None:
                images_instances_ids.append(image_import_instance.instance.id)

            if hasattr(image_import_instance, 'media_assign'):
                images_instances_associations_ids.append(image_import_instance.media_assign.id)

        self.image_instances = Image.objects.filter(id__in=images_instances_ids)
        self.images_associations_instances = MediaProductThrough.objects.filter(id__in=images_instances_associations_ids)

    def set_prices(self):
        sales_price_ids = []
        for price in self.prices:
            image_import_instance = ImportSalesPriceInstance(price, product=self.instance, import_process=self.import_process)
            image_import_instance.process()

    def set_variations(self):
        from .variations import ImportConfiguratorVariationsInstance, ImportConfigurableVariationInstance

        if hasattr(self, 'configurator_select_values') and not hasattr(self, 'variations') and self.rule:
            variation_import = ImportConfiguratorVariationsInstance(
                {'values': self.configurator_select_values},
                import_process=self.import_process,
                rule=self.rule,
                config_product=self.instance,
            )
            variation_import.process()
            self.variations_products_instances = variation_import.variations
            return

        variation_products_ids = []
        if hasattr(self, 'variations'):
            for variation_data in self.variations:
                variation_import = ImportConfigurableVariationInstance(
                    variation_data,
                    import_process=self.import_process,
                    config_product=self.instance,
                    sales_channel=self.sales_channel,
                )

                variation_import.process()
                variation_products_ids.append(variation_import.instance.variation.id)

        self.variations_products_instances = Product.objects.filter(id__in=variation_products_ids)

    def set_bundle_variations(self):
        from .variations import ImportBundleVariationInstance

        variation_products_ids = []

        if hasattr(self, 'bundle_variations'):
            for variation_data in self.bundle_variations:
                variation_import = ImportBundleVariationInstance(
                    variation_data,
                    import_process=self.import_process,
                    bundle_product=self.instance,
                    sales_channel=self.sales_channel,
                )
                variation_import.process()
                variation_products_ids.append(variation_import.instance.variation.id)

        self.bundle_variations_instances = Product.objects.filter(id__in=variation_products_ids)

    def set_alias_variations(self):
        from .variations import ImportAliasVariationInstance

        variation_products_ids = []
        if hasattr(self, 'alias_variations'):
            for variation_data in self.alias_variations:
                variation_import = ImportAliasVariationInstance(
                    variation_data,
                    import_process=self.import_process,
                    parent_product=self.instance,
                    sales_channel=self.sales_channel,
                )
                variation_import.process()
                variation_products_ids.append(variation_import.instance.id)

        self.alias_variations_instances = Product.objects.filter(id__in=variation_products_ids)

    def set_rule_product_property(self):

        rule_product_property, _ = ProductProperty.objects.get_or_create(
            multi_tenant_company=self.config_product.multi_tenant_company,
            product=self.instance,
            property=Property.objects.get(multi_tenant_company=self.config_product.multi_tenant_company, is_product_type=True),
        )

        if rule_product_property.value_select != self.rule.product_type:
            rule_product_property.value_select = self.rule.product_type
            rule_product_property.save()

    def _handle_parent_sku_links(self):

        parent_sku = self.data.get("configurable_parent_sku")
        if parent_sku:
            parent = Product.objects.filter(sku=parent_sku, multi_tenant_company=self.multi_tenant_company).first()
            if parent and parent.is_configurable():
                ConfigurableVariation.objects.get_or_create(
                    parent=parent,
                    variation=self.instance,
                    multi_tenant_company=self.multi_tenant_company,
                )
                return

        parent_sku = self.data.get("bundle_parent_sku")
        if parent_sku:
            parent = Product.objects.filter(sku=parent_sku, multi_tenant_company=self.multi_tenant_company).first()
            if parent and parent.is_bundle():
                BundleVariation.objects.get_or_create(
                    parent=parent,
                    variation=self.instance,
                    multi_tenant_company=self.multi_tenant_company,
                )
                return

    def post_process_logic(self):

        if self.type == Product.SIMPLE:
            self.update_ean_code()

        if hasattr(self, 'translations') and not self.created:
            self.update_translations()

        self.set_product_properties()

        if hasattr(self, 'images'):
            self.set_images()

        if hasattr(self, 'prices'):
            self.set_prices()

        if (hasattr(self, 'variations') or hasattr(self, 'configurator_select_values')) and self.type == Product.CONFIGURABLE:
            self.set_variations()

        if self.type == Product.BUNDLE and hasattr(self, 'bundle_variations'):
            self.set_bundle_variations()

        if hasattr(self, 'alias_variations'):
            self.set_alias_variations()

        self._handle_parent_sku_links()

    def update_translations(self):
        translation_instance_ids = []

        for translation in self.translations:
            try:
                import_instance = ImportProductTranslationInstance(translation, self.import_process, product=self.instance, sales_channel=self.sales_channel)
                import_instance.process()
            except IntegrityError as e:
                if "url_key" in str(e):
                    # Try again with url_key removed
                    translation = translation.copy()
                    translation["url_key"] = None
                    import_instance = ImportProductTranslationInstance(translation, self.import_process, product=self.instance, sales_channel=self.sales_channel)
                    import_instance.process()
                else:
                    raise

            translation_instance_ids.append(import_instance.instance.id)

        self.translation_instances = ProductTranslation.objects.filter(id__in=translation_instance_ids)

    def create_translations(self):
        translation_instance_ids = []

        for translation in self.translations:
            name = translation.get('name') or getattr(self, 'name', 'Unnamed')
            short_description = translation.get('short_description')
            description = translation.get('description')
            url_key = translation.get('url_key')
            language = translation.get('language') or self.language

            translation_obj, created = ProductTranslation.objects.get_or_create(
                multi_tenant_company=self.instance.multi_tenant_company,
                language=language,
                product=self.instance,
                name=name,
                sales_channel=self.sales_channel,
            )

            # Update other fields if created or if missing
            updated = False
            if created or translation_obj.short_description != short_description:
                translation_obj.short_description = short_description
                updated = True
            if created or translation_obj.description != description:
                translation_obj.description = description
                updated = True
            if created or translation_obj.url_key != url_key:
                translation_obj.url_key = url_key
                updated = True

            try:
                if updated:
                    translation_obj.save()
            except IntegrityError as e:
                if "url_key" in str(e):
                    # Try saving again with a blank/null url_key
                    translation_obj.url_key = None
                    translation_obj.save()
                else:
                    raise


            bullet_points = translation.get('bullet_points')
            if bullet_points is not None:
                translation_obj.bullet_points.all().delete()
                for index, text in enumerate(bullet_points):
                    ProductTranslationBulletPoint.objects.create(
                        multi_tenant_company=translation_obj.multi_tenant_company,
                        product_translation=translation_obj,
                        text=text,
                        sort_order=index,
                    )

            translation_instance_ids.append(translation_obj.id)

        self.translation_instances = ProductTranslation.objects.filter(id__in=translation_instance_ids)


class ImportProductTranslationInstance(AbstractImportInstance):
    def __init__(self, data: dict, import_process=None, product=None, instance=None, sales_channel=None):
        super().__init__(data, import_process, instance)
        self.product = product
        self.sales_channel = sales_channel

        self.set_field_if_exists('name')
        self.set_field_if_exists('short_description')
        self.set_field_if_exists('description')
        self.set_field_if_exists('url_key')
        self.set_field_if_exists('language')
        self.set_field_if_exists('product_data')
        self.set_field_if_exists('bullet_points')

        self.validate()
        self._set_product_import_instance()

    @property
    def local_class(self):
        return ProductTranslation

    @property
    def updatable_fields(self):
        return ['name', 'short_description', 'description', 'url_key']

    def validate(self):
        """
        Validate that the 'value' key exists.
        """
        if not hasattr(self, 'name'):
            raise ValueError("The 'name' field is required.")

        if not getattr(self, 'product_data', None) and not self.product:
            raise ValueError("Either a 'product' or 'product_data' must be provided.")

    def _set_product_import_instance(self):

        if not self.product:
            self.product_import_instance = ImportProductInstance(self.product_data, self.import_process)

    def pre_process_logic(self):

        if not self.product:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

    def process_logic(self):
        fac = ProductTranslationImport(self, self.import_process, instance=self.instance)
        fac.run()

        self.instance = fac.instance

        if hasattr(self, 'bullet_points') and self.bullet_points is not None:
            self.instance.bullet_points.all().delete()
            for index, text in enumerate(self.bullet_points):
                ProductTranslationBulletPoint.objects.create(
                    product_translation=self.instance,
                    text=text,
                    sort_order=index,
                )


class ImportSalesPriceInstance(AbstractImportInstance):
    def __init__(self, data: dict, import_process=None, product=None, currency_object=None, instance=None):
        super().__init__(data, import_process, instance)
        self.product = product

        self.set_field_if_exists('rrp')
        self.set_field_if_exists('price')
        self.set_field_if_exists('currency')
        self.set_field_if_exists('product_data')

        if currency_object:
            self.currency = currency_object
        else:
            self._set_public_currency()
            self._set_currency()

        self.validate()
        self._set_product_import_instance()

    @property
    def local_class(self):
        return SalesPrice

    @property
    def updatable_fields(self):
        return ['rrp', 'price']

    def validate(self):
        """
        Validate that the 'value' key exists.
        """
        if not hasattr(self, 'rrp') and not hasattr(self, 'price'):
            raise ValueError("Both 'rrp' and 'price' cannot be None.")

        if getattr(self, 'rrp', None) is None and getattr(self, 'price', None) is None:
            raise ValueError("Both 'rrp' and 'price' cannot be None.")

        if not getattr(self, 'product_data', None) and not self.product:
            raise ValueError("Either a 'product' or 'product_data' must be provided.")

        if hasattr(self, 'currency') and getattr(self, 'currency', None) is None:
            raise ValueError("Both 'currency' cannot be None.")

    def _set_public_currency(self):

        if hasattr(self, 'currency'):
            self.public_currency = PublicCurrency.objects.filter(iso_code=self.currency).first()

            if self.public_currency is None:
                raise ValueError("The price use unsupported currency.")

    def _set_currency(self):

        if not hasattr(self, 'currency'):
            self.currency = Currency.objects.get(multi_tenant_company=self.multi_tenant_company, is_default_currency=True)
            return

        if hasattr(self, 'currency') and hasattr(self, 'public_currency'):

            self.currency = Currency.objects.get(
                multi_tenant_company=self.multi_tenant_company,
                iso_code=self.public_currency.iso_code,
            )

            return

        raise ValueError("There is no way to receive the currency.")

    def _set_product_import_instance(self):

        if not self.product:
            self.product_import_instance = ImportProductInstance(self.product_data, self.import_process)

    def pre_process_logic(self):
        if not self.product:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

        rrp = getattr(self, 'rrp', None)
        price = getattr(self, 'price', None)

        try:
            if rrp is not None:
                rrp = Decimal(rrp)
            if price is not None:
                price = Decimal(price)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid numeric value for price or rrp: rrp={rrp}, price={price}")

        # Case 1: Only one is provided -> use that as the sale price.
        if rrp is not None and price is None:
            self.price = rrp
            self.rrp = None
        elif price is not None and rrp is not None:
            # Both are provided; ensure rrp is the higher value.
            if rrp < price:
                # Swap them so that rrp becomes the higher number.
                self.rrp, self.price = price, rrp
            else:
                self.rrp = rrp
                self.price = price

    def process_logic(self):

        # we will skip the price if is 0 because we can't create price 0
        if self.price == 0:
            return

        fac = SalesPriceImport(self, self.import_process, instance=self.instance)
        fac.run()
