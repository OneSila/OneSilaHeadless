import math
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import Optional
from django.core.exceptions import ValidationError
from magento.models import ProductAttribute, AttributeOption, AttributeSet, TaxClass
from core.helpers import clean_json_data
from currencies.models import Currency
from sales_channels.factories.imports.decorators import if_allowed_by_saleschannel
from sales_channels.factories.imports import SalesChannelImportMixin
from core.mixins import TemporaryDisableInspectorSignalsMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportPropertyInstance, ImportPropertySelectValueInstance, \
    ImportProductPropertiesRuleInstance, ImportProductPropertiesRuleItemInstance
from products.models import Product
from properties.models import Property, PropertySelectValue, ProductPropertiesRuleItem, ProductPropertiesRule
from sales_channels.integrations.magento2.constants import PROPERTY_FRONTEND_INPUT_MAP
from sales_channels.integrations.magento2.factories.imports.properties import ImportMagentoProductPropertiesRuleInstance
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProperty, MagentoPropertySelectValue, \
    MagentoAttributeSetImport, MagentoProduct, MagentoSalesChannelView
from sales_channels.integrations.magento2.models.products import MagentoEanCode, MagentoPrice, MagentoProductContent, \
    MagentoImageProductAssociation
from sales_channels.integrations.magento2.models.properties import MagentoAttributeSet, MagentoProductProperty
from sales_channels.integrations.magento2.models.sales_channels import MagentoRemoteLanguage
from sales_channels.integrations.magento2.models.taxes import MagentoTaxClass, MagentoCurrency
from sales_channels.models import ImportProperty, ImportPropertySelectValue, ImportProduct, SalesChannelViewAssign, \
    SalesChannelImport
from django.contrib.contenttypes.models import ContentType
from magento.models import Product as MagentoApiProduct
from magento.models import ConfigurableProduct as MagentoApiConfigurableProduct
from sales_channels.models.products import RemoteProductConfigurator
import logging
import traceback

from taxes.models import VatRate

logger = logging.getLogger(__name__)


class MagentoImportProcessor(TemporaryDisableInspectorSignalsMixin, SalesChannelImportMixin, GetMagentoAPIMixin):
    remote_ean_code_class = MagentoEanCode
    remote_imageproductassociation_class = MagentoImageProductAssociation
    remote_price_class = MagentoPrice

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, sales_channel, language)
        self.remote_local_property_map = {}

    def prepare_import_process(self):
        """
        This method starts off with gathering the configuration from the frontend
        wizard and collecting the pieces in order to do the import cleanly.

        There is also a bunch of magento currency and multi-langual preperation done
        in order to structer the data correctly during the import.
        """
        super().prepare_import_process()
        # get properties
        self.properties = ImportProperty.objects.filter(import_process=self.import_process)

        # get select values
        properties_to_import = []
        for p in self.properties:
            if p.raw_data['frontend_input'] in [ProductAttribute.SELECT, ProductAttribute.MULTISELECT]:
                properties_to_import.append(p.raw_data['attribute_code'])

        properties_string = ",".join(properties_to_import)
        api_properties = self.api.product_attributes.add_criteria(
            field="attribute_code",
            value=properties_string,
            condition="in").all_in_memory()

        self.rules = self.api.product_attribute_set.all_in_memory()
        self.products_cnt = self.api.products.count()

        magento_languages = MagentoRemoteLanguage.objects.filter(
            sales_channel=self.sales_channel,
            local_instance__isnull=False
        )

        magento_currencies = MagentoCurrency.objects.filter(
            sales_channel=self.sales_channel,
            local_instance__isnull=False
        )

        self.magento_translation_id_map = {}
        self.magento_translation_store_code_map = {}
        self.magento_scope_currency_map = {}

        seen_languages = set()
        seen_currencies = set()
        store_view_codes = []

        for magento_language in magento_languages:

            store_view_codes.append(magento_language.store_view_code)
            if magento_language.local_instance in seen_languages:
                continue

            self.magento_translation_id_map[magento_language.remote_id] = magento_language.local_instance
            self.magento_translation_store_code_map[magento_language.store_view_code] = magento_language.local_instance
            seen_languages.add(magento_language.local_instance)

        for magento_currency in magento_currencies:
            currency = magento_currency.local_instance
            if currency in seen_currencies:
                continue

            for store_view_code in store_view_codes:
                if store_view_code in magento_currency.store_view_codes:
                    self.magento_scope_currency_map[store_view_code] = (currency, magento_currency.remote_id)
                    seen_currencies.add(currency)
                    break  # Stop once we assigned this currency

        self.select_values = []
        if len(self.magento_translation_store_code_map) == 1:
            # Only one language configured → no need to handle per-language translations
            for property in api_properties:
                for option in property.options:
                    self.select_values.append(option)
        else:
            for property in api_properties:
                option_translation_map = defaultdict(dict)  # value_id => {lang: label}
                option_objects = {}  # value_id => base option from scope='all'

                # Fetch base options from scope='all'
                try:
                    base_options = property.get_options_with_scope(scope="all")
                except Exception as e:
                    logger.debug(f"Failed to fetch base options for property {property.attribute_code}: {e}")
                    continue

                for option in base_options:
                    value_id = option.value
                    if value_id == '':
                        continue
                    option_objects[value_id] = option  # store only base version

                # Collect translations per store view
                for store_code, local_lang in self.magento_translation_store_code_map.items():
                    try:
                        scoped_options = property.get_options_with_scope(scope=store_code)
                    except Exception as e:
                        logger.debug(f"Failed to fetch options for scope {store_code}: {e}")
                        continue

                    for option in scoped_options:
                        value_id = option.value
                        label = option.label
                        if not label or value_id == '':
                            continue

                        option_translation_map[value_id][local_lang] = label

                # Combine base with translations
                for value_id, base_option in option_objects.items():
                    base_option.translations = option_translation_map.get(value_id, {})
                    self.select_values.append(base_option)

    def get_total_instances(self):
        properties_cnt = self.properties.count()
        return properties_cnt + len(self.select_values) + len(self.rules) + self.products_cnt

    def get_properties_data(self):
        return self.properties

    def get_structured_property_data(self, property_data: ImportProperty):
        reversed_frontend_input_map = {
            value: key
            for key, value in PROPERTY_FRONTEND_INPUT_MAP.items()
        }
        reversed_frontend_input_map['weight'] = Property.TYPES.FLOAT

        raw = property_data.raw_data
        structured = {}

        structured['internal_name'] = raw.get('attribute_code')
        structured['name'] = raw.get('default_frontend_label')
        structured['is_public_information'] = True
        structured['add_to_filters'] = bool(int(raw.get('is_filterable', False)))

        translations = []
        frontend_labels = raw.get('frontend_labels', [])
        for frontend_label in frontend_labels:
            language = self.magento_translation_id_map.get(str(frontend_label['store_id']))
            translation_data = {
                'name': frontend_label['label'],
                'language': language
            }
            translations.append(translation_data)

        if translations:
            structured['translations'] = translations

        # Try to detect type from frontend_input
        frontend_input = raw.get('frontend_input')
        if frontend_input in reversed_frontend_input_map:
            structured['type'] = reversed_frontend_input_map[frontend_input]

        property_data.structured_data = structured
        return property_data

    def get_final_property_data_from_log(self, log_instance: ImportProperty):
        return log_instance.structured_data

    def update_property_import_instance(self, import_instance: ImportPropertyInstance):
        import_instance.prepare_mirror_model_class(
            mirror_model_class=MagentoProperty,
            sales_channel=self.sales_channel,
            mirror_model_map={
                "attribute_code": "internal_name",
                "local_instance": "*"
            }
        )

    def update_property_log_instance(self, log_instance: ImportProperty, import_instance: ImportPropertyInstance):
        mirror_property = import_instance.remote_instance

        log_instance.successfully_imported = True
        log_instance.content_type = ContentType.objects.get_for_model(import_instance.instance)
        log_instance.object_id = import_instance.instance.pk

        if mirror_property:
            log_instance.remote_property = mirror_property

        log_instance.save()

        if mirror_property and not mirror_property.remote_id:
            mirror_property.remote_id = log_instance.raw_data['attribute_id']
            mirror_property.save()

        self.remote_local_property_map[log_instance.raw_data['attribute_code']] = {
            "local": import_instance.instance,
            "remote": mirror_property
        }

    def get_select_values_data(self):
        return self.select_values

    def get_structured_select_value_data(self, value_data: AttributeOption):

        structured_data = {
            'value': value_data.label,
        }

        if hasattr(value_data, 'translations'):
            translations = []
            for language, value in value_data.translations.items():
                translations.append({'language': language, 'value': value})

            structured_data['translations'] = translations

        log_instance = ImportPropertySelectValue.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            raw_data=value_data.data,
            import_process=self.import_process,
            structured_data=structured_data
        )

        return log_instance

    def get_final_select_value_data_from_log(self, log_instance: ImportPropertySelectValue):
        return log_instance.structured_data

    def get_select_value_property_instance(self, log_instance: ImportPropertySelectValue, value_data: AttributeOption):
        property_map = self.remote_local_property_map.get(value_data.attribute.attribute_code, {})
        return property_map.get('local', None)

    def update_property_select_value_import_instance(self, import_instance: ImportPropertySelectValueInstance,
                                                     value_data: AttributeOption):
        property_map = self.remote_local_property_map.get(value_data.attribute.attribute_code, {})
        remote_property = property_map.get('remote', None)

        import_instance.prepare_mirror_model_class(
            mirror_model_class=MagentoPropertySelectValue,
            sales_channel=self.sales_channel,
            mirror_model_map={
                "local_instance": "*",
            },
            mirror_model_defaults={
                "remote_property": remote_property
            }
        )

    def import_rules_process(self):
        for rule_data in self.rules:
            log_instance, items = self.get_structured_rule_data(rule_data)

            structured_data = log_instance.structured_data.copy()
            structured_data["items"] = items

            import_instance = ImportMagentoProductPropertiesRuleInstance(
                structured_data,
                self.import_process,
                sales_channel=self.sales_channel
            )

            import_instance.process()
            self.update_percentage()
            self.update_rule_log_instance(log_instance, import_instance, rule_data)

    def build_items_data(self, rule_data):
        structured_items = []
        real_items = []

        for magento_attribute in rule_data.get_attributes():
            attr_code = magento_attribute.attribute_code
            if attr_code in self.remote_local_property_map:
                property_instance = self.remote_local_property_map[attr_code]["local"]

                structured_items.append({
                    "property": property_instance.internal_name
                })

                real_items.append({
                    "property": property_instance
                })

        return structured_items, real_items

    def get_structured_rule_data(self, rule_data: AttributeSet):
        structured_items, real_items = self.build_items_data(rule_data)

        structured_data = {
            'value': rule_data.attribute_set_name,
            'items': structured_items,
        }

        log_instance = MagentoAttributeSetImport.objects.create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            import_process=self.import_process,
            raw_data=rule_data.data,
            structured_data=structured_data
        )

        return log_instance, real_items

    def update_rule_log_instance(self, log_instance: MagentoAttributeSetImport,
                                 import_instance: ImportProductPropertiesRuleInstance, rule_data: AttributeSet):

        mirror_rule_value = import_instance.remote_instance

        log_instance.successfully_imported = True
        log_instance.content_type = ContentType.objects.get_for_model(import_instance.instance)
        log_instance.object_id = import_instance.instance.pk

        if mirror_rule_value:
            log_instance.remote_attribute_set = mirror_rule_value

        log_instance.save()

        if mirror_rule_value:
            to_save = False
            if not mirror_rule_value.remote_id:
                mirror_rule_value.remote_id = rule_data.attribute_set_id
                to_save = True

            if not mirror_rule_value.group_remote_id:
                group = rule_data.get_or_create_group_by_name('OneSila')
                mirror_rule_value.group_remote_id = group.attribute_group_id
                to_save = True

            if to_save:
                mirror_rule_value.save()

    def get_product_translation_map(self, product: MagentoApiProduct) -> dict | None:
        """
        Returns a mapping of local language → scoped MagentoApiProduct
        without mutating the original product.
        """
        if len(self.magento_translation_store_code_map) == 1:
            return None

        self.translation_product_map = {}

        for store_code, language in self.magento_translation_store_code_map.items():
            try:
                translated_product = deepcopy(product)
                translated_product.refresh(scope=store_code)
                self.translation_product_map[language] = translated_product
            except Exception as e:
                logger.debug(f"Failed to fetch translation for scope {store_code}: {e}")
                continue

        return self.translation_product_map

    def get_product_currency_map(self, product: MagentoApiProduct) -> dict | None:
        """
        Returns a mapping of local currency → scoped MagentoApiProduct,
        reusing translation-product mapping where possible.
        """
        if len(self.magento_scope_currency_map) == 0:
            return None

        if self.sales_channel.is_single_currency():
            return None

        currency_product_map = {}

        for store_code, currency_tuple in self.magento_scope_currency_map.items():
            currency = currency_tuple[0]
            website_id = int(currency_tuple[1])

            if website_id not in product.views:
                continue

            # Reuse from translation map if available
            reused_translation = None
            if hasattr(self, 'self.translation_product_map') and store_code in self.magento_translation_store_code_map:
                language = self.magento_translation_store_code_map[store_code]
                reused_translation = self.translation_product_map.get(language)

            if reused_translation:
                currency_product_map[currency] = reused_translation
                continue

            try:
                refreshed_product = deepcopy(product)
                refreshed_product.refresh(scope=store_code)
                currency_product_map[currency] = refreshed_product
            except Exception as e:
                logger.debug(f"Failed to fetch currency-scoped product for scope {store_code}: {e}")
                continue

        return currency_product_map

    def get_product_translations(self, product: MagentoApiProduct, translation_product_map=None):
        if translation_product_map is None:
            return [{
                "name": product.name,
                "short_description": product.short_description,
                "description": product.description,
                "url_key": product.url_key,
            }]
        else:
            translations = []
            for language, scoped_product in translation_product_map.items():
                translations.append({
                    "language": language,
                    "name": scoped_product.name,
                    "short_description": scoped_product.short_description,
                    "description": scoped_product.description,
                    "url_key": scoped_product.url_key,
                })

            return translations

    def get_product_images(self, product: MagentoApiProduct):
        images = []
        image_id_map = {}

        for index, image_entry in enumerate(product.media_gallery_entries):
            image_data = {
                "image_url": image_entry.link,
                "sort_order": image_entry.position
            }

            if image_entry.is_thumbnail:
                image_data['is_main_image'] = True

            images.append(image_data)
            image_id_map[str(index)] = image_entry.id

        return images, image_id_map

    def get_product_attributes(self, custom_attributes: dict, translation_product_map: Optional[dict] = None,
                               product_sku: Optional[str] = None):
        attributes = []
        mirror_map = {}
        accepted_properties = self.remote_local_property_map.keys()

        for attribute_code in accepted_properties:

            if attribute_code not in custom_attributes:
                continue

            magento_value = custom_attributes[attribute_code]
            value = magento_value
            value_is_id = False
            property = self.remote_local_property_map[attribute_code]["local"]
            magento_property = self.remote_local_property_map[attribute_code]["remote"]

            translations = []

            # Handle SELECT and MULTISELECT
            if property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
                value_is_id = True

                if property.type == Property.TYPES.SELECT:
                    try:
                        magento_select_value = MagentoPropertySelectValue.objects.get(
                            sales_channel=self.sales_channel,
                            multi_tenant_company=self.import_process.multi_tenant_company,
                            remote_property=magento_property,
                            remote_id=magento_value
                        )
                        value = magento_select_value.local_instance.id
                    except MagentoPropertySelectValue.DoesNotExist:
                        self.register_missing_select_value_record(
                            product_sku=product_sku,
                            attribute_code=attribute_code,
                            magento_property=magento_property,
                            magento_value=magento_value,
                        )

                        if not self.import_process.skip_broken_records:
                            raise

                        continue

                else:  # MULTISELECT
                    select_values_ids = magento_value.split(',')
                    select_values = PropertySelectValue.objects.filter(
                        remotepropertyselectvalue__sales_channel=self.sales_channel,
                        remotepropertyselectvalue__remote_property=magento_property,
                        remotepropertyselectvalue__remote_id__in=select_values_ids
                    )
                    value = select_values.values_list('id', flat=True)

            # Handle TEXT / DESCRIPTION multilingual
            elif property.type in [Property.TYPES.DESCRIPTION, Property.TYPES.TEXT] and translation_product_map:
                for language, scoped_product in translation_product_map.items():
                    # language-specific value for the attribute
                    lang_value = scoped_product.custom_attributes.get(attribute_code)
                    if lang_value:
                        translations.append({
                            "language": language,
                            "value": lang_value,
                        })

            attribute_data = {
                "value": value,
                "value_is_id": value_is_id,
                "property": property,
            }

            if len(translations):
                attribute_data["translations"] = translations

            attributes.append(attribute_data)

            mirror_map[property.id] = {
                "remote_property": magento_property,
                "remote_value": str(magento_value),
            }

        return attributes, mirror_map

    def register_missing_select_value_record(self, product_sku: Optional[str], attribute_code: str,
                                             magento_property: MagentoProperty, magento_value):
        record = {
            "step": "product_attributes",
            "sku": product_sku,
            "attribute_code": attribute_code,
            "remote_property_id": getattr(magento_property, "remote_id", None),
            "remote_value": str(magento_value),
            "error": "MagentoPropertySelectValue matching query does not exist.",
        }

        self._broken_records.append(record)

    def register_product_processing_error(self, product: MagentoApiProduct, exc: Exception):
        record = {
            "step": "product_import",
            "sku": getattr(product, "sku", None),
            "remote_id": getattr(product, "id", None) or getattr(product, "entity_id", None),
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

        self._broken_records.append(record)

    def get_product_prices(self, product: MagentoApiProduct,
                           currency_product_map=None):
        """
        Returns a list of price entries.

        - If `currency_product_map` is provided, returns one price entry per currency.
        - If not, falls back to a single price using the default currency and given product.
        """
        prices = []

        if currency_product_map:
            for currency, scoped_product in currency_product_map.items():
                try:
                    prices.append({
                        "price": scoped_product.special_price,
                        "rrp": scoped_product.price,
                        "currency": currency.iso_code,
                    })
                except Exception as e:
                    logger.debug(f"Failed to extract price for currency {currency.iso_code}: {e}")
                    continue
        else:
            try:
                currency = Currency.objects.get(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    is_default_currency=True
                )
                prices.append({
                    "price": product.special_price,
                    "rrp": product.price,
                    "currency": currency.iso_code,
                })
            except Exception as e:
                logger.debug(f"Failed to fallback to default currency pricing: {e}")

        return prices

    def get_product_variations(self, product: MagentoApiProduct, rule: ProductPropertiesRule):
        variations = []
        sku_to_id_map = {}

        for child in product.get_children():
            variation_data = self.get_product_data(child, rule)

            if not variation_data:
                continue

            variations.append({
                "variation_data": variation_data,
            })
            sku_to_id_map[variation_data['sku']] = {
                "id": child.id,
                "sku": child.sku,
            }

        return variations, sku_to_id_map

    def sync_configurator_rule_items(self, product: MagentoApiProduct, rule):
        configurable_prod = MagentoApiConfigurableProduct(product=product, client=self.api)

        for option in configurable_prod.options:
            property = Property.objects.filter(
                multi_tenant_company=self.import_process.multi_tenant_company,
                remoteproperty__sales_channel=self.sales_channel,
                remoteproperty__remote_id=option['attribute_id']
            ).first()

            if property:
                rule_item_import_instance = ImportProductPropertiesRuleItemInstance(
                    data={"type": ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR},
                    import_process=self.import_process,
                    rule=rule,
                    property=property,
                )
                rule_item_import_instance.process()

    @if_allowed_by_saleschannel('sync_ean_codes')
    def get_product_ean_code(self, custom_attributes: dict) -> Optional[str]:
        """
        Returns the EAN code from custom_attributes if present and syncing is enabled.
        """
        ean_code_key = self.sales_channel.ean_code_attribute
        if ean_code_key in custom_attributes:
            return custom_attributes[ean_code_key]

    def get_vat_name(self, custom_attributes: dict) -> Optional[str]:
        if 'tax_class_id' in custom_attributes:
            tax_class_id = custom_attributes.get('tax_class_id')

            try:
                tax_class_id = int(tax_class_id)
            except (ValueError, TypeError):
                pass

            return self.tax_map.get(tax_class_id, None)

        return None

    def get_product_data(self, product: MagentoApiProduct, rule: ProductPropertiesRule):
        type_map = {
            MagentoApiProduct.PRODUCT_TYPE_SIMPLE: Product.SIMPLE,
            MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE: Product.CONFIGURABLE,
        }

        product_type = type_map.get(product.type_id, None)

        if product_type is None:
            return False

        custom_attributes = product.custom_attributes

        structured_data = {
            "name": product.name,
            "sku": product.sku,
            "type": product_type,
            "active": bool(product.status),
            "allow_backorder": product.backorders,
        }

        translation_map = self.get_product_translation_map(product)
        currency_map = self.get_product_currency_map(product)

        ean_code = self.get_product_ean_code(custom_attributes)
        if ean_code:
            structured_data['ean_code'] = ean_code

        structured_data['translations'] = self.get_product_translations(product, translation_map)
        structured_data['images'], structured_data['__image_index_to_remote_id'] = self.get_product_images(product)

        if product_type == Product.SIMPLE:
            structured_data['properties'], structured_data['__mirror_product_properties_map'] = self.get_product_attributes(custom_attributes, translation_map, product.sku)
            structured_data['prices'] = self.get_product_prices(product, currency_map)

        elif product_type == Product.CONFIGURABLE:
            structured_data['variations'], structured_data['__variation_sku_to_id_map'] = self.get_product_variations(product, rule)
            self.sync_configurator_rule_items(product, rule)

        structured_data['vat_rate'] = self.get_vat_name(custom_attributes)
        structured_data['use_vat_rate_name'] = True

        return structured_data

    def handle_attributes(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'properties'):
            product_properties = import_instance.product_property_instances
            remote_product = import_instance.remote_instance
            mirror_map = import_instance.data.get('__mirror_product_properties_map', {})

            for product_property in product_properties:
                mirror_data = mirror_map.get(product_property.property.id)

                if not mirror_data:
                    continue  # skip if we didn't get original remote context

                remote_property = mirror_data["remote_property"]
                remote_value = mirror_data["remote_value"]

                remote_product_property, _ = MagentoProductProperty.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=product_property,
                    remote_product=remote_product,
                    remote_property=remote_property,
                )

                if not remote_product_property.remote_value:
                    remote_product_property.remote_value = remote_value
                    remote_product_property.save()

    def handle_images(self, import_instance: ImportProductInstance):
        if hasattr(import_instance, 'images'):
            remote_id_map = import_instance.data.get('__image_index_to_remote_id', {})

            index = 0
            for image_ass in import_instance.images_associations_instances:
                magento_image_association, _ = MagentoImageProductAssociation.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=image_ass,
                    remote_product=import_instance.remote_instance,
                )

                remote_id = remote_id_map.get(str(index))
                if remote_id and not magento_image_association.remote_id:
                    magento_image_association.remote_id = remote_id
                    magento_image_association.save()

                index += 1

    def handle_variations(self, import_instance: ImportProductInstance, rule: ProductPropertiesRule):
        if hasattr(import_instance, 'variations'):
            variation_id_map = import_instance.data.get('__variation_sku_to_id_map', {})
            remote_product = import_instance.remote_instance
            variations = import_instance.variations_products_instances

            for product in variations:
                info_map = variation_id_map.get(product.sku, {})
                remote_sku = info_map.get('sku', None)
                remote_id = info_map.get('id', None)

                if remote_sku and remote_id:

                    magento_product, _ = MagentoProduct.objects.get_or_create(
                        multi_tenant_company=self.import_process.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        local_instance=product,
                        remote_sku=remote_sku,
                        is_variation=True
                    )

                    magento_product.remote_parent_product = remote_product
                    magento_product.remote_id = remote_id
                    magento_product.save()

            if hasattr(remote_product, 'configurator'):
                configurator = remote_product.configurator
                configurator.update_if_needed(rule=rule, variations=variations, send_sync_signal=False)
            else:
                RemoteProductConfigurator.objects.create_from_remote_product(
                    remote_product=import_instance.remote_instance,
                    rule=rule,
                    variations=variations,
                )

    def handle_sales_channels_views(self, import_instance: ImportProductInstance, product: MagentoApiProduct):
        sales_channel_views = MagentoSalesChannelView.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id__in=product.views
        )

        for sales_channel_view in sales_channel_views:
            SalesChannelViewAssign.objects.get_or_create(
                product=import_instance.instance,
                sales_channel_view=sales_channel_view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                remote_product=import_instance.remote_instance,
                sales_channel=self.sales_channel,
            )

    def update_remote_product(self, import_instance: ImportProductInstance, product: MagentoApiProduct, is_variation: bool):
        remote_product = import_instance.remote_instance

        if not remote_product.remote_id:
            remote_product.remote_id = product.id

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation

        remote_product.save()

    def get_product_rule(self, product: MagentoApiProduct):
        magento_rule = MagentoAttributeSet.objects.get(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=product.attribute_set_id
        )
        return magento_rule.local_instance

    def is_magento_variation(self, product: MagentoApiProduct) -> bool:
        is_variation = product.visibility == MagentoApiProduct.VISIBILITY_NOT_VISIBLE and product.type_id == MagentoApiProduct.PRODUCT_TYPE_SIMPLE

        if product.type_id == MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE:
            self.configurable_skus.add(product.sku)

        return is_variation

    def set_taxes_map(self):
        self.tax_map = {}

        tax_classes = self.api.taxes.all_in_memory()
        for tax_class in tax_classes:
            if tax_class.class_type == TaxClass.CLASS_TYPE_PRODUCT:
                local_instance, _ = VatRate.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    name=tax_class.class_name
                )

                remote_instance, _ = MagentoTaxClass.objects.get_or_create(
                    multi_tenant_company=self.import_process.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=local_instance,
                    remote_id=tax_class.class_id
                )

                self.tax_map[tax_class.class_id] = tax_class.class_name

    def import_products_process(self):
        self.set_taxes_map()

        products_api = self.api.products
        products_api.clear_pagination()
        products_api.per_page = 200

        # Fetch first page
        product_batch = products_api.add_criteria(
            field="type_id",
            value=f"{MagentoApiProduct.PRODUCT_TYPE_SIMPLE},{MagentoApiProduct.PRODUCT_TYPE_CONFIGURABLE}",
            condition="in").execute_search()

        self.configurable_skus = set()

        while True:
            if not product_batch:
                break

            if not isinstance(product_batch, list):
                product_batch = [product_batch]

            for product in product_batch:
                try:
                    is_variation = self.is_magento_variation(product)
                    rule = self.get_product_rule(product)
                    structured_data = self.get_product_data(product, rule)

                    if not structured_data:
                        continue

                    product_import_instance = ImportProductInstance(
                        data=structured_data,
                        import_process=self.import_process,
                        rule=rule,
                    )

                    # This is creating the remote_id and is actually
                    # your "import_instance".
                    product_import_instance.prepare_mirror_model_class(
                        mirror_model_class=MagentoProduct,
                        sales_channel=self.sales_channel,
                        mirror_model_map={
                            "local_instance": "*",
                        },
                        mirror_model_defaults={
                            "remote_sku": product.sku,
                        }
                    )

                    product_import_instance.process()

                    self.update_remote_product(product_import_instance, product, is_variation)
                    self.create_log_instance(product_import_instance, structured_data)
                    self.handle_ean_code(product_import_instance)
                    self.handle_attributes(product_import_instance)
                    self.handle_translations(product_import_instance)
                    self.handle_prices(product_import_instance)
                    self.handle_images(product_import_instance)
                    self.handle_variations(product_import_instance, rule)

                    if not is_variation:
                        self.handle_sales_channels_views(product_import_instance, product)

                    self.update_percentage()
                except Exception as exc:
                    self.register_product_processing_error(product, exc)
                    if not self.import_process.skip_broken_records:
                        raise
                    continue

            try:
                product_batch = products_api.next()
            except ValueError:
                break
