from core.tests import TestCase
from imports_exports.factories.variations import (
    ImportConfigurableVariationInstance,
    ImportConfiguratorVariationsInstance,
    ImportBundleVariationInstance,
    ImportAliasVariationInstance,
)
from imports_exports.models import Import
from products.models import Product, ConfigurableVariation, BundleVariation
from properties.models import PropertySelectValue, Property


# The process test is done inside products
class ImportVariationInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        # Dummy product for tests
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE
        )

        self.variation = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE
        )

        property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="color",
            type="SELECT"
        )

        # Dummy select value
        self.select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=property,
        )

    def test_configurable_variation_with_both_products(self):
        instance = ImportConfigurableVariationInstance(
            {},
            import_process=self.import_process,
            config_product=self.product,
            variation_product=self.variation
        )
        self.assertEqual(instance.config_product, self.product)
        self.assertEqual(instance.variation_product, self.variation)

    def test_configurable_variation_with_missing_config_product(self):
        data = {
            "variation_data": {
                "name": "Variation A",
                "sku": "SKU-A"
            }
        }
        with self.assertRaises(ValueError) as cm:
            ImportConfigurableVariationInstance(data, self.import_process)
        self.assertIn("config_product", str(cm.exception))

    def test_configurable_variation_with_missing_variation_product(self):
        data = {
            "config_product_data": {
                "name": "Config",
                "sku": "SKU-CONFIG"
            }
        }
        with self.assertRaises(ValueError) as cm:
            ImportConfigurableVariationInstance(data, self.import_process)
        self.assertIn("variation_product", str(cm.exception))

    def test_configurator_variation_with_full_data(self):
        data = {
            "config_product_data": {
                "name": "T-Shirt",
                "sku": "SKU-001",
                "type": Product.CONFIGURABLE
            },
            "rule_data": {
                "value": "T-Shirt",
                "require_ean_code": True,
                "items": [
                    {"type": "REQUIRED", "property_data": {"name": "Size", "type": "SELECT"}}
                ]
            },
            "values": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"},
                {"property_data": {"name": "Size", "type": "SELECT"}, "value": "Large"}
            ]
        }

        instance = ImportConfiguratorVariationsInstance(data, self.import_process)
        self.assertEqual(instance.values[0]["value"], "Red")

    def test_configurator_variation_missing_config_product(self):
        data = {
            "rule_data": {"value": "Shoes"},
            "values": [{"property_data": {"name": "Color"}, "value": "Blue"}]
        }
        with self.assertRaises(ValueError) as cm:
            ImportConfiguratorVariationsInstance(data, self.import_process)
        self.assertIn("config_product", str(cm.exception))

    def test_configurator_variation_missing_rule(self):
        data = {
            "config_product_data": {"name": "Shoes", "sku": "SKU-SHOES"},
            "values": [{"property_data": {"name": "Color"}, "value": "Blue"}]
        }
        with self.assertRaises(ValueError) as cm:
            ImportConfiguratorVariationsInstance(data, self.import_process)
        self.assertIn("rule", str(cm.exception))

    def test_configurator_variation_missing_values(self):
        data = {
            "config_product_data": {"name": "Shoes", "sku": "SKU-SHOES"},
            "rule_data": {"value": "Shoes"}
        }
        with self.assertRaises(ValueError) as cm:
            ImportConfiguratorVariationsInstance(data, self.import_process)
        self.assertIn("select_values", str(cm.exception))


class ImportVariationUpdateOnlyTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            update_only=True,
        )

        self.config_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="CFG-001",
        )

        self.bundle_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.BUNDLE,
            sku="BND-001",
        )

        self.parent_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="PRD-001",
        )

    def test_configurable_variation_created_when_update_only(self):
        data = {"variation_data": {"name": "Variation A", "sku": "VAR-A"}}
        instance = ImportConfigurableVariationInstance(
            data, self.import_process, config_product=self.config_product
        )
        instance.process()

        variation = Product.objects.get(sku="VAR-A")
        self.assertTrue(
            ConfigurableVariation.objects.filter(
                parent=self.config_product, variation=variation
            ).exists()
        )

    def test_bundle_variation_created_when_update_only(self):
        data = {"variation_data": {"name": "Bundle Var", "sku": "VAR-B"}}
        instance = ImportBundleVariationInstance(
            data, self.import_process, bundle_product=self.bundle_product
        )
        instance.process()

        variation = Product.objects.get(sku="VAR-B")
        self.assertTrue(
            BundleVariation.objects.filter(
                parent=self.bundle_product, variation=variation
            ).exists()
        )

    def test_alias_variation_created_when_update_only(self):
        data = {"variation_data": {"name": "Alias Var", "sku": "VAR-C"}}
        instance = ImportAliasVariationInstance(
            data, self.import_process, parent_product=self.parent_product
        )
        instance.process()

        alias_product = Product.objects.get(sku="VAR-C")
        self.assertEqual(alias_product.alias_parent_product, self.parent_product)
