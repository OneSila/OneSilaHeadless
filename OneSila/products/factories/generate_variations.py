from django.conf import settings

from products.models import Product, ProductTranslation, ConfigurableVariation
from properties.models import ProductPropertiesRuleItem, ProductProperty


class GenerateProductVariations:
    def __init__(self, rule, config_product, select_values, language=None):
        self.rule = rule
        self.config_product = config_product
        self.select_values = select_values
        self.multi_tenant_company = self.config_product.multi_tenant_company

        if language:
            self.language = language
        else:
            if self.multi_tenant_company:
                self.language = self.multi_tenant_company.language
            else:
                self.language = settings.LANGUAGE_CODE

    def set_configurator_rule_items(self):

        self.rule_items = ProductPropertiesRuleItem.objects.filter(
            rule=self.rule,
            type__in=[ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR, ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR]
        )

    def group_select_values(self):
        self.grouped_values = []
        for item in self.rule_items:
            values = self.select_values.filter(property=item.property)

            if not values.exists():
                continue

            property_grouped_values = {
                'property': item.property,
                'values': values,
            }
            self.grouped_values.append(property_grouped_values)

    def _get_value_combinations(self):
        from itertools import product

        if not self.grouped_values:
            return []

        # Each element in product() will be a tuple like (red, large)
        value_sets = [group['values'] for group in self.grouped_values]
        return list(product(*value_sets))

    def generate_variations(self):
        combinations = self._get_value_combinations()
        ids = []

        for combo in combinations:

            # 1. Create Product
            variation = Product.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Product.SIMPLE,
                active=True,
                vat_rate=self.config_product.vat_rate,
            )

            # 2. Create Translation
            translated_base_name = self.config_product._get_translated_value(field_name='name', language=self.language)
            combo_names = ' x '.join([sv._get_translated_value(field_name='value',
                                                               language=self.language,
                                                               related_name='propertyselectvaluetranslation_set') for sv in combo])
            name = f"{translated_base_name} ({combo_names})"

            ProductTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                language=self.language,
                name=name,
                short_description='',
                description='',
                url_key=None,
            )

            # 3. Add rule type to ProductProperty
            ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=variation,
                property=self.rule.product_type.property,
                value_select=self.rule.product_type,
            )

            # 4. Add each selected value
            for sv in combo:
                ProductProperty.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product=variation,
                    property=sv.property,
                    value_select=sv,
                )

            # 5. Link to config_product as a ConfigurableVariation
            ConfigurableVariation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                parent=self.config_product,
                variation=variation
            )

            ids.append(variation.id)

        self.variations = Product.objects.filter(id__in=ids)

    def run(self):
        self.set_configurator_rule_items()
        self.group_select_values()
        self.generate_variations()
