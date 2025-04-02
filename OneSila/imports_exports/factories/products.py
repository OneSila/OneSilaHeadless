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
from products.models import Product, ProductTranslation
from properties.models import Property, ProductPropertiesRuleItem, ProductProperty
from sales_prices.models import SalesPrice
from taxes.models import VatRate


class ProductImport(ImportOperationMixin):
    get_identifiers = ['sku', 'type']


class ProductTranslationImport(ImportOperationMixin):
    get_identifiers = ['product']


class SalesPriceImport(ImportOperationMixin):
    get_identifiers = ['product', 'currency']


class ImportProductInstance(AbstractImportInstance):

    def __init__(self, data: dict, import_process=None, rule=None, translations=None):
        super().__init__(data, import_process)

        if translations is None:
            translations = []

        self.rule = rule
        self.translations = translations

        default_sku = shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(7)
        self.set_field_if_exists('name')
        self.set_field_if_exists('sku', default_sku)
        self.set_field_if_exists('type', default_value=Product.SIMPLE)

        self.set_field_if_exists('active')
        self.set_field_if_exists('vat_rate')
        self.set_field_if_exists('ean_code')
        self.set_field_if_exists('allow_backorder')

        # it's the rule
        self.set_field_if_exists('product_type')
        self.set_field_if_exists('attributes')

        self.set_field_if_exists('translations')

        self.set_field_if_exists('images')
        self.set_field_if_exists('prices')

        self.set_field_if_exists('variations')
        self.set_field_if_exists('configurator_select_values')

        # used to help remote imports
        self.set_field_if_exists('__image_index_to_remote_id')
        self.set_field_if_exists('__mirror_product_properties_map')
        self.set_field_if_exists('__variation_sku_to_id_map')

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

        if hasattr(self, 'type') and self.type not in [Product.SIMPLE, Product.CONFIGURABLE]:
            raise ValueError("Invalid 'type' value.")


    def _set_vat_rate(self):

        if hasattr(self, 'vat_rate'):

            if isinstance(self.vat_rate, str):
                self.vat_rate = int(self.vat_rate)

            vat_rate_object, _ = VatRate.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                rate=self.vat_rate)

            self.vat_rate = vat_rate_object

            self.vat_rate_instance = self.vat_rate


    def update_ean_code(self):

        if hasattr(self, 'ean_code'):

            self.ean_code_instance = EanCode.objects.filter(
                multi_tenant_company=self.multi_tenant_company,
                product=self.instance,
            ).first()

            if self.ean_code_instance is None:
                self.ean_code_instance = EanCode.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product=self.instance,
                    ean_code=self.ean_code)

                self.ean_code_instance.already_used= True
                self.ean_code_instance.internal= False
            else:
                if self.ean_code_instance.ean_code != self.ean_code:
                    self.ean_code_instance.ean_code = self.ean_code

                self.ean_code_instance.already_used = True
                self.ean_code_instance.internal = False
                self.ean_code_instance.save()


    def _set_rule(self):

        if self.rule:
            return

        if hasattr(self, 'product_type'):
            required_names = set()
            if hasattr(self, 'configurator_select_values'):
                for select_value in self.configurator_select_values:
                    prop_data = select_value['property_data']
                    name = prop_data.get("name")
                    required_names.add(name)


            items = []
            if hasattr(self, 'attributes'):
                for attribute in self.attributes:
                    if 'property_data' in attribute:
                        name = attribute['property_data'].get("name")
                        item_data = {
                            'property_data': attribute['property_data'],
                            'type': ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR if name in required_names else ProductPropertiesRuleItem.OPTIONAL

                        }
                        items.append(item_data)


            rule_import_instance = ImportProductPropertiesRuleInstance({"value": self.product_type, "items": items}, self.import_process)
            rule_import_instance.process()
            self.rule = rule_import_instance.instance

        self.rule_instance = self.rule


    def _set_translations(self):

        if not hasattr(self, 'translations') or not len(self.translations):

            self.translations = [{
                'name': getattr(self, 'name', 'Unnamed'),
                'language': self.language
            }]


    def pre_process_logic(self):
        self._set_vat_rate()
        self._set_rule()
        self._set_translations()


    def process_logic(self):
        fac = ProductImport(self, self.import_process)
        fac.run()

        # Save the created/updated instance.
        self.instance = fac.instance
        self.created = fac.created

        if self.created:
            self.create_translations()

    def set_product_properties(self):

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
        product_property_import_instance.process()

        product_property_ids = []
        if self.type == Product.SIMPLE and hasattr(self, 'attributes'):

            for attribute in self.attributes:
                product_property_import_instance = ImportProductPropertyInstance(
                    attribute,
                    self.import_process,
                    product=self.instance)

                product_property_import_instance.process()
                product_property_ids.append(product_property_import_instance.instance.id)

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

            images_instances_ids.append(image_import_instance.instance.id)
            if hasattr(image_import_instance, 'media_assign'):
                images_instances_associations_ids.append(image_import_instance.media_assign.id)

        self.image_instances = Image.objects.filter(id__in=images_instances_ids)
        self.images_associations_instances  = MediaProductThrough.objects.filter(id__in=images_instances_associations_ids)



    def set_prices(self):
        sales_price_ids = []
        for price in self.prices:
            image_import_instance = ImportSalesPriceInstance(price, product=self.instance, import_process=self.import_process)
            image_import_instance.process()

    def set_variations(self):
        from .variations import ImportConfiguratorVariationsInstance, ImportConfigurableVariationInstance


        if hasattr(self, 'configurator_select_values') and not hasattr(self, 'variations') and self.rule:
            variation_import = ImportConfiguratorVariationsInstance(
                { 'values': self.configurator_select_values },
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
                )
                variation_import.process()
                variation_products_ids.append(variation_import.instance.variation.id)

        self.variations_products_instances = Product.objects.filter(id__in=variation_products_ids)


    def set_rule_product_property(self):

        rule_product_property, _ = ProductProperty.objects.get_or_create(
            multi_tenant_company=self.config_product.multi_tenant_company,
            product=self.instance,
            property=Property.objects.get(multi_tenant_company=self.config_product.multi_tenant_company, is_product_type=True),
        )

        if rule_product_property.value_select != self.rule.product_type:
            rule_product_property.value_select = self.rule.product_type
            rule_product_property.save()

    def post_process_logic(self):

        if self.type == Product.SIMPLE:
            self.update_ean_code()

        if hasattr(self, 'translations') and not self.created:
            self.update_translations()

        if self.rule:
            self.set_product_properties()

        if hasattr(self, 'images'):
            self.set_images()

        if hasattr(self, 'prices'):
           self.set_prices()

        if (hasattr(self, 'variations') or hasattr(self, 'configurator_select_values')) and self.type == Product.CONFIGURABLE:
            self.set_variations()


    def update_translations(self):
        translation_instance_ids = []

        for translation in self.translations:
            try:
                import_instance = ImportProductTranslationInstance(translation, self.import_process, product=self.instance)
                import_instance.process()
            except IntegrityError as e:
                if "url_key" in str(e):
                    # Try again with url_key removed
                    translation = translation.copy()
                    translation["url_key"] = None
                    import_instance = ImportProductTranslationInstance(translation, self.import_process, product=self.instance)
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

            translation_instance_ids.append(translation_obj.id)

        self.translation_instances = ProductTranslation.objects.filter(id__in=translation_instance_ids)


class ImportProductTranslationInstance(AbstractImportInstance):

    def __init__(self, data: dict, import_process=None, product=None):
        super().__init__(data, import_process)
        self.product = product

        self.set_field_if_exists('name')
        self.set_field_if_exists('short_description')
        self.set_field_if_exists('description')
        self.set_field_if_exists('url_key')
        self.set_field_if_exists('product_data')

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
        fac = ProductTranslationImport(self, self.import_process)
        fac.run()

        self.instance= fac.instance

class ImportSalesPriceInstance(AbstractImportInstance):

    def __init__(self, data: dict, import_process=None, product=None, currency_object=None):
        super().__init__(data, import_process)
        self.product = product

        self.set_field_if_exists('rrp')
        self.set_field_if_exists('price')
        self.set_field_if_exists('currency')
        self.set_field_if_exists('product_data')

        self.validate()
        self._set_product_import_instance()

        if currency_object:
            self.currency = currency_object
        else:
            self._set_public_currency()
            self._set_currency()

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
        if not hasattr(self, 'rrp') and  not hasattr(self, 'price') :
            raise ValueError("Both 'rrp' and 'price' cannot be None.")

        if getattr(self, 'rrp', None) is None and getattr(self, 'price', None) is None:
            raise ValueError("Both 'rrp' and 'price' cannot be None.")

        if not getattr(self, 'product_data', None) and not self.product:
            raise ValueError("Either a 'product' or 'product_data' must be provided.")


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

            self.currency, _ = Currency.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                iso_code=self.public_currency.iso_code,
                name=self.public_currency.name,
                symbol=self.public_currency.symbol,
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

        fac = SalesPriceImport(self, self.import_process)
        fac.run()