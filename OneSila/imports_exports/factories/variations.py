from imports_exports.factories.mixins import AbstractImportInstance, ImportOperationMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.properties import ImportProductPropertiesRuleInstance, ImportPropertyInstance, \
    GetSelectValueMixin
from products.factories.generate_variations import GenerateProductVariations
from products.models import ConfigurableVariation
from properties.models import PropertySelectValue, ProductProperty, Property


class ConfigurableVariationImport(ImportOperationMixin):
    get_identifiers = ['parent', 'variation']
    allow_edit = False


class ImportConfigurableVariationInstance(AbstractImportInstance):
    """
    Import instance for assigning a single variation to a configurable product.

    Required:
        - `config_product_data` or `config_product`
        - `variation_data` or `variation_product`
    """

    def __init__(self, data: dict, import_process=None, config_product=None, variation_product=None):
        super().__init__(data, import_process)
        self.config_product = config_product
        self.variation_product = variation_product

        self.set_field_if_exists('variation_data')
        self.set_field_if_exists('config_product_data')

        self.validate()
        self._set_products_import_instance()

    @property
    def local_class(self):
        return ConfigurableVariation

    def validate(self):
        if not (self.config_product or hasattr(self, 'config_product_data')):
            raise ValueError("You must provide either `config_product` or `config_product_data`.")

        if not (self.variation_product or hasattr(self, 'variation_data')):
            raise ValueError("You must provide either `variation_product` or `variation_data`.")

    def _set_products_import_instance(self):
        if not self.config_product and hasattr(self, 'config_product_data'):
            self.config_product_import_instance = ImportProductInstance(self.config_product_data, self.import_process)

        if not self.variation_product and hasattr(self, 'variation_data'):
            self.variation_import_instance = ImportProductInstance(self.variation_data, self.import_process)

    def pre_process_logic(self):
        if not self.config_product:
            self.config_product_import_instance.process()
            self.config_product = self.config_product_import_instance.instance

        if not self.variation_product:
            self.variation_import_instance.process()
            self.variation_product = self.variation_import_instance.instance

    def process_logic(self):

        # this are needed for ConfigurableVariationImport
        self.parent = self.config_product
        self.variation = self.variation_product

        fac = ConfigurableVariationImport(self, self.import_process)
        fac.run()

        self.instance = fac.instance

        rule = self.config_product.get_product_rule()
        if rule:
            # if we created that we might want to add the
            rule_product_property, _ = ProductProperty.objects.get_or_create(
                multi_tenant_company=self.config_product.multi_tenant_company,
                product=self.variation_product,
                property=Property.objects.get(multi_tenant_company=self.config_product.multi_tenant_company, is_product_type=True),
            )

            if rule_product_property.value_select != rule.product_type:
                rule_product_property.value_select = rule.product_type
                rule_product_property.save()


class ImportConfiguratorVariationsInstance(AbstractImportInstance, GetSelectValueMixin):
    """
    Import instance for auto-generating multiple variations for a configurable product.

    Required:
        - `config_product_data` or `config_product`
        - `rule_data` or `rule`
        - `values` (list of dicts) or `select_values` (actual PropertySelectValue objects)

    Example input:
    {
        "config_product_data": { ... },
        "rule_data": {
            "value": "T-Shirt",
            "require_ean_code": True,
            "items": [ ... ]
        },
        "values": [
            { "property_data": { "name": "Color" }, "value": "Red" },
            { "property_data": { "name": "Size" }, "value": "Large" }
        ]
    }
    """

    def __init__(self, data: dict, import_process=None, config_product=None, rule=None, select_values=None):
        super().__init__(data, import_process)
        self.config_product = config_product
        self.rule = rule
        self.select_values = select_values

        self.set_field_if_exists('config_product_data')
        self.set_field_if_exists('rule_data')
        self.set_field_if_exists('values')

        self.validate()
        self._set_config_product_instance()

    def validate(self):
        if not (self.config_product or hasattr(self, 'config_product_data')):
            raise ValueError("Must provide either `config_product` or `config_product_data`.")

        if not (self.rule or hasattr(self, 'rule_data')):
            raise ValueError("Must provide either `rule` or `rule_data`.")

        if not (self.select_values or hasattr(self, 'values')):
            raise ValueError("Must provide either `select_values` or `values`.")

    def _set_config_product_instance(self):
        if not self.config_product and hasattr(self, 'config_product_data'):
            self.config_product_import_instance = ImportProductInstance(self.config_product_data, self.import_process)

    def _set_rule(self):
        if self.rule:
            return

        if hasattr(self, 'rule_data'):
            rule_import = ImportProductPropertiesRuleInstance(self.rule_data, self.import_process)
            rule_import.process()
            self.rule = rule_import.instance

    def _set_select_values(self):

        if self.select_values is None and hasattr(self, 'values'):
            ids = []
            for value in self.values:
                if 'property_data' in value and 'value' in value:
                    property_import_instance = ImportPropertyInstance(value['property_data'], self.import_process)
                    property_import_instance.process()
                    property = property_import_instance.instance

                    select_value = self.get_select_value(value['value'], property=property)
                    ids.append(select_value.id)

            self.select_values = PropertySelectValue.objects.filter(id__in=ids)

    def pre_process_logic(self):
        self._set_rule()
        self._set_select_values()

        if not self.config_product:
            self.config_product_import_instance.process()
            self.config_product = self.config_product_import_instance.instance

    def process_logic(self):

        factory = GenerateProductVariations(
            rule=self.rule,
            config_product=self.config_product,
            select_values=self.select_values,
            language=self.language
        )
        factory.run()
        self.variations = factory.variations