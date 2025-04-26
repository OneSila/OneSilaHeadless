from core.tests import TestCase
from currencies.models import PublicCurrency, Currency
from eancodes.models import EanCode
from imports_exports.factories.products import ImportProductInstance, ImportProductTranslationInstance, \
    ImportSalesPriceInstance
from imports_exports.models import Import
from media.models import MediaProductThrough
from products.models import Product, ProductTranslation, ConfigurableVariation
from properties.models import ProductPropertiesRuleItem, ProductPropertiesRule, PropertySelectValue, \
    PropertySelectValueTranslation, Property, ProductProperty
from sales_prices.models import SalesPrice
from currencies.currencies import currencies


class ImportProductInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_missing_name_raises_error(self):
        data = {
            "sku": "SKU123",
            "type": "SIMPLE"
        }

        with self.assertRaises(ValueError) as cm:
            ImportProductInstance(data, self.import_process)

        self.assertIn("The 'name' field is required", str(cm.exception))

    def test_valid_with_name_and_sku(self):
        data = {
            "name": "Test Product",
            "sku": "SKU123"
        }

        instance = ImportProductInstance(data, self.import_process)
        self.assertEqual(instance.name, "Test Product")
        self.assertEqual(instance.sku, "SKU123")
        self.assertEqual(instance.type, Product.SIMPLE)  # default type

    def test_configurable_product_type(self):
        data = {
            "name": "Config Product",
            "type": "CONFIGURABLE"
        }

        instance = ImportProductInstance(data, self.import_process)
        self.assertEqual(instance.type, Product.CONFIGURABLE)

    def test_invalid_type_raises_error(self):
        data = {
            "name": "Invalid Type Product",
            "type": "BUNDLE"
        }

        with self.assertRaises(ValueError) as cm:
            ImportProductInstance(data, self.import_process)

        self.assertIn("Invalid 'type' value", str(cm.exception))

    def test_most_fields_completed(self):
        data = {
            "name": "Fancy Product",
            "sku": "SKU987",
            "type": "SIMPLE",
            "active": True,
            "vat_rate": 19,
            "ean_code": "1234567890123",
            "allow_backorder": False,
            "product_type": "Chair",
            "attributes": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"},
                {"property_data": {"name": "Material", "type": "SELECT", "value": "Metal"}},
            ],
            "translations": [
                {
                    "short_description": "Short desc",
                    "description": "Longer description",
                    "url_key": "fancy-product"
                }
            ],
            "images": [
                {"image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg"},
                {"image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True}
            ],
            "prices": [
                {"price": 12.99, "currency": "EUR"},
                {"price": 15.99, "currency": "USD"}
            ],
            "variations": [
                {"name": "Variant 1"},
                {"name": "Variant 2"},
            ],
            "configurator_select_values": [
                {"property_data": {"name": "Size"}, "value": "Large"},
                {"property_data": {"name": "Color"}, "value": "Blue"},
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        self.assertEqual(instance.name, "Fancy Product")
        self.assertEqual(instance.sku, "SKU987")
        self.assertTrue(instance.active)
        self.assertFalse(instance.allow_backorder)
        self.assertEqual(instance.vat_rate, 19)  # raw value, will be converted in pre_process
        self.assertEqual(instance.ean_code, "1234567890123")
        self.assertEqual(len(instance.attributes), 2)
        self.assertEqual(len(instance.images), 2)
        self.assertEqual(len(instance.prices), 2)
        self.assertEqual(len(instance.variations), 2)
        self.assertEqual(len(instance.configurator_select_values), 2)



class ImportProductTranslationAndSalesPriceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        # Create a basic product to test direct product vs product_data
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="test123"
        )

        self.default_currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            iso_code="EUR",
            name="Euro",
            symbol="€",
            is_default_currency=True
        )

        self.public_currency = PublicCurrency.objects.create(
            iso_code="EUR",
            name="Euro",
            symbol="€"
        )

    # ------------------------
    # Translation tests
    # ------------------------

    def test_translation_with_direct_product(self):
        data = {
            "name": "Product Name",
            "short_description": "Short",
            "description": "Full desc",
            "url_key": "product-name"
        }
        instance = ImportProductTranslationInstance(data, self.import_process, product=self.product)
        self.assertEqual(instance.name, "Product Name")

    def test_translation_with_product_data(self):
        data = {
            "name": "Translated Product",
            "product_data": {
                "name": "Inner Product"
            }
        }
        instance = ImportProductTranslationInstance(data, self.import_process)
        self.assertEqual(instance.name, "Translated Product")
        self.assertIn("product_data", instance.data)

    def test_translation_missing_name_raises(self):
        data = {
            "product_data": { "name": "Something" }
        }
        with self.assertRaises(ValueError) as cm:
            ImportProductTranslationInstance(data, self.import_process)

        self.assertIn("The 'name' field is required", str(cm.exception))

    def test_translation_missing_product_and_data_raises(self):
        data = {
            "name": "Should Fail"
        }
        with self.assertRaises(ValueError) as cm:
            ImportProductTranslationInstance(data, self.import_process)

        self.assertIn("Either a 'product' or 'product_data' must be provided", str(cm.exception))

    # ------------------------
    # Sales price tests
    # ------------------------

    def test_sales_price_with_direct_product(self):
        data = {
            "price": 50,
            "currency": "EUR"
        }
        instance = ImportSalesPriceInstance(data, self.import_process, product=self.product)
        self.assertEqual(instance.price, 50)

    def test_sales_price_with_product_data(self):
        data = {
            "price": 120,
            "currency": "EUR",
            "product_data": {
                "name": "Inner Product Price"
            }
        }
        instance = ImportSalesPriceInstance(data, self.import_process)
        self.assertEqual(instance.price, 120)
        self.assertEqual(instance.currency.iso_code, "EUR")

    def test_sales_price_missing_both_rrp_and_price_raises(self):
        data = {
            "currency": "EUR",
            "product_data": {
                "name": "Some"
            }
        }
        with self.assertRaises(ValueError) as cm:
            ImportSalesPriceInstance(data, self.import_process)

        self.assertIn("Both 'rrp' and 'price' cannot be None", str(cm.exception))

    def test_sales_price_missing_product_and_data_raises(self):
        data = {
            "price": 30,
            "currency": "EUR"
        }
        with self.assertRaises(ValueError) as cm:
            ImportSalesPriceInstance(data, self.import_process)

        self.assertIn("Either a 'product' or 'product_data' must be provided", str(cm.exception))

    def test_sales_price_with_only_rrp(self):
        data = {
            "rrp": 100,
            "currency": "EUR",
            "product_data": { "name": "RRP Product" }
        }
        instance = ImportSalesPriceInstance(data, self.import_process)
        instance.pre_process_logic()
        self.assertEqual(instance.price, 100)
        self.assertIsNone(instance.rrp)

    def test_sales_price_with_price_and_rrp_swapped(self):
        data = {
            "rrp": 80,
            "price": 100,
            "currency": "EUR",
            "product_data": { "name": "Swapped Product" }
        }
        instance = ImportSalesPriceInstance(data, self.import_process)
        instance.pre_process_logic()
        self.assertEqual(instance.rrp, 100)
        self.assertEqual(instance.price, 80)

    def test_sales_price_with_invalid_currency_raises(self):
        data = {
            "price": 10,
            "currency": "XXX",
            "product_data": { "name": "Invalid Currency" }
        }

        with self.assertRaises(ValueError) as cm:
            ImportSalesPriceInstance(data, self.import_process)

        self.assertIn("The price use unsupported currency", str(cm.exception))


class ImportProductInstanceProcessTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )

        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
            value="Chair"
        )

    def test_create_new_product(self):
        data = {
            "name": "New Product",
            "sku": "NEW001"
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertIsNotNone(instance.instance)
        self.assertEqual(instance.instance.name, "New Product")
        self.assertEqual(instance.instance.sku, "NEW001")

    def test_edit_existing_product(self):
        existing = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="EXIST123",
            type=Product.SIMPLE
        )

        translation = ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=existing,
            name="Old Name"
        )

        data = {
            "name": "Updated Name",
            "sku": "EXIST123"
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        existing.refresh_from_db()
        self.assertEqual(existing.name, "Updated Name")
        self.assertEqual(instance.instance.pk, existing.pk)

    def test_edit_ean_code(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="EAN001",
            type=Product.SIMPLE
        )
        data = {
            "name": "With EAN",
            "sku": "EAN001",
            "ean_code": "999888777"
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()
        ean = EanCode.objects.filter(product=product).first()
        self.assertEqual(ean.ean_code, "999888777")

    def test_create_product_with_given_rule(self):
        rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value
        )
        data = {
            "name": "With Rule",
            "sku": "RULE123"
        }

        instance = ImportProductInstance(data, self.import_process, rule=rule)
        instance.process()

        self.assertEqual(instance.rule.pk, rule.pk)

    def test_create_product_using_product_type(self):
        data = {
            "name": "Using Product Type",
            "sku": "TYPE123",
            "product_type": "Chair2"
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(ProductPropertiesRule.objects.filter(product_type__id=instance.rule.product_type.id).exists())

    def test_create_product_with_translations(self):
        data = {
            "name": "Translated Product",
            "sku": "TRANS123",
            "translations": [
                {
                    "short_description": "Short Desc",
                    "description": "Long Desc",
                    "url_key": "translated-product"
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        translation = ProductTranslation.objects.filter(product=instance.instance).first()
        self.assertEqual(translation.short_description, "Short Desc")

    def test_create_product_with_images(self):
        data = {
            "name": "Image Product",
            "sku": "IMG001",
            "images": [
                { "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg" },
                { "image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(MediaProductThrough.objects.filter(product=instance.instance).exists())

    def test_create_product_with_prices(self):
        data = {
            "name": "Priced Product",
            "sku": "PRICE001",
            "prices": [
                {"price": 10.99, "currency": "EUR"},
                {"price": 15.99, "currency": "USD"}
            ]
        }

        Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            **currencies['US']
        )

        Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            **currencies['DE']
        )

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(SalesPrice.objects.filter(product=instance.instance).count() >= 2)

    def test_create_product_with_attributes_and_rule(self):
        data = {
            "name": "Attr Product",
            "sku": "ATTR123",
            "product_type": "Chair",
            "attributes": [
                { "property_data": { "name": "Color", "type": "SELECT" }, "value": "Red" },
                { "property_data": { "name": "Size", "type": "SELECT" }, "value": "M" },
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(ProductPropertiesRuleItem.objects.filter(rule=instance.rule).count() >= 2)

    def test_create_configurable_with_configurator_variations(self):
        data = {
            "name": "Configurable Auto Variants",
            "sku": "CFG-AUTO",
            "type": Product.CONFIGURABLE,
            "product_type": "Chair",
            "attributes": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"}
            ],
            "configurator_select_values": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"}
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        config_product = instance.instance
        variations = ConfigurableVariation.objects.filter(parent=config_product)

        self.assertEqual(config_product.type, Product.CONFIGURABLE)
        self.assertEqual(variations.count(), 1)
        self.assertEqual(variations.first().variation.name, "Configurable Auto Variants (Red)")


    def test_create_configurable_with_manual_variations(self):
        data = {
            "name": "Configurable Manual Variants",
            "sku": "CFG-MANUAL",
            "type": Product.CONFIGURABLE,
            "product_type": "Chair",
            "attributes": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"}
            ],
            "variations": [
                {
                    'variation_data': {"name": "Red Variant"}
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        config_product = instance.instance
        variations = ConfigurableVariation.objects.filter(parent=config_product)

        self.assertEqual(config_product.type, Product.CONFIGURABLE)
        self.assertEqual(variations.count(), 1)
        self.assertEqual(variations.first().variation.name, "Red Variant")


    def test_full_example(self):

        data = {
            "name": "Ultimate Product",
            "sku": "ALL001",
            "type": Product.CONFIGURABLE,
            "product_type": "Chair",
            "ean_code": "111222333",
            "vat_rate": 19,
            "active": True,
            "allow_backorder": False,
            "translations": [
                {
                    "short_description": "All features",
                    "description": "This product has everything.",
                    "url_key": "ultimate-product"
                }
            ],
            "attributes": [
                { "property_data": { "name": "Material", "type": "SELECT" }, "value": "Red" },
                { "property_data": { "name": "Style", "type": "SELECT" }, "value": "Elegant" }
            ],
            "images": [
                { "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg" },
                { "image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True }
            ],
            "prices": [
                { "price": 29.99, "currency": "EUR" },
                { "rrp": 34.99, "currency": "USD" }
            ],
            "configurator_select_values": [
                { "property_data": { "name": "Style", "type": "SELECT" }, "value": "Elegant" }
            ]
        }
        Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            **currencies['US']
        )

        Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            **currencies['DE']
        )

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(ProductTranslation.objects.filter(product=instance.instance).exists())
        self.assertTrue(MediaProductThrough.objects.filter(product=instance.instance).exists())
        self.assertTrue(SalesPrice.objects.filter(product=instance.instance).count() >= 2)
        self.assertTrue(ConfigurableVariation.objects.filter(parent=instance.instance).exists())
        self.assertTrue(ProductPropertiesRuleItem.objects.filter(rule=instance.rule).count() >= 2)
        self.assertTrue(ProductProperty.objects.filter(product=instance.instance).count() >= 1)