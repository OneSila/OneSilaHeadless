from core.tests import TestCase
from currencies.models import PublicCurrency, Currency
from eancodes.models import EanCode
from imports_exports.factories.mixins import UpdateOnlyInstanceNotFound
from imports_exports.factories.products import ImportProductInstance, ImportProductTranslationInstance, \
    ImportSalesPriceInstance
from imports_exports.models import Import
from media.models import MediaProductThrough
from products.models import Product, ProductTranslation, ConfigurableVariation, BundleVariation
from properties.models import ProductPropertiesRuleItem, ProductPropertiesRule, PropertySelectValue, \
    PropertySelectValueTranslation, Property, ProductProperty
from sales_prices.models import SalesPrice
from currencies.currencies import currencies
from core.exceptions import ValidationError


class ImportProductInstanceValidateTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_missing_name_creates_no_translation(self):
        data = {
            "sku": "SKU123",
            "type": "SIMPLE"
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.pre_process_logic()

        self.assertFalse(hasattr(instance, 'name'))
        self.assertEqual(instance.translations, [])

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
            "type": "SOMETYPE"
        }

        with self.assertRaises(ValueError) as cm:
            ImportProductInstance(data, self.import_process)

        self.assertIn("Invalid 'type' value", str(cm.exception))

    def test_most_fields_completed(self):
        data = {
            "name": "Fancy Product",
            "sku": "SKU987",
            "type": "CONFIGURABLE",
            "active": True,
            "vat_rate": 19,
            "ean_code": "1234567890123",
            "allow_backorder": False,
            "product_type": "Chair",
            "properties": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"},
                {"property_data": {"name": "Material", "type": "SELECT", "value": "Metal"}},
            ],
            "translations": [
                {
                    "name": "Fancy Product",
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
                {"price": 12.99, "currency": "USD"},
            ],
            "variations": [
                {
                    'variation_data': {"name": "Variant 1"}
                },
                {
                    'variation_data': {"name": "Variant 2"}
                }
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
        self.assertEqual(len(instance.properties), 2)
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

        self.default_currency, _ = Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
            **currencies['GB']
        )

        self.public_currency, _ = PublicCurrency.objects.get_or_create(
            iso_code="GBP",
            name="Pound",
            symbol="£"
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
            "product_data": {"name": "Something"}
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
            "product_data": {"name": "RRP Product"}
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
            "product_data": {"name": "Swapped Product"}
        }
        instance = ImportSalesPriceInstance(data, self.import_process)
        instance.pre_process_logic()
        self.assertEqual(instance.rrp, 100)
        self.assertEqual(instance.price, 80)

    def test_sales_price_with_invalid_currency_raises(self):
        data = {
            "price": 10,
            "currency": "XXX",
            "product_data": {"name": "Invalid Currency"}
        }

        with self.assertRaises(ValidationError) as cm:
            ImportSalesPriceInstance(data, self.import_process)

        self.assertIn("unknown in the public currency list", str(cm.exception))


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

    def test_create_product_with_bullet_points(self):
        data = {
            "name": "Bullet Product",
            "sku": "BULLET001",
            "translations": [
                {
                    "bullet_points": ["Point A", "Point B"]
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        translation = ProductTranslation.objects.filter(product=instance.instance).first()
        bullet_texts = list(translation.bullet_points.order_by('sort_order').values_list('text', flat=True))
        self.assertEqual(bullet_texts, ["Point A", "Point B"])

    def test_create_product_with_images(self):
        data = {
            "name": "Image Product",
            "sku": "IMG001",
            "images": [
                {"image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg"},
                {"image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True}
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        self.assertTrue(
            MediaProductThrough.objects.get_product_images(
                product=instance.instance,
                sales_channel=None,
            ).exists()
        )

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
            "properties": [
                {"property_data": {"name": "Color", "type": "SELECT"}, "value": "Red"},
                {"property_data": {"name": "Size", "type": "SELECT"}, "value": "M"},
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
            "properties": [
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
            "properties": [
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

    def test_create_bundle_with_manual_variations_and_quantity(self):
        data = {
            "name": "Bundle Desk Set",
            "sku": "BND-SET",
            "type": Product.BUNDLE,
            "product_type": "Desk Set",
            "properties": [
                {"property_data": {"name": "Size", "type": "SELECT"}, "value": "Large"}
            ],
            "bundle_variations": [
                {
                    "variation_data": {
                        "name": "Chair - Large"
                    },
                    "quantity": 2
                },
                {
                    "variation_data": {
                        "name": "Table - Large"
                    },
                    "quantity": 1
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        bundle_product = instance.instance
        variations = BundleVariation.objects.filter(parent=bundle_product)

        self.assertEqual(bundle_product.type, Product.BUNDLE)
        self.assertEqual(variations.count(), 2)

        quantities = sorted([v.quantity for v in variations])
        self.assertEqual(quantities, [1, 2])
        self.assertSetEqual(set(v.variation.name for v in variations), {"Chair - Large", "Table - Large"})

    def test_update_bundle_variation_quantity(self):
        # Step 1: Create initial bundle with variation
        initial_data = {
            "name": "Bundle Monitor Set",
            "sku": "BND-MONITOR",
            "type": Product.BUNDLE,
            "product_type": "Monitor Setup",
            "bundle_variations": [
                {
                    "variation_data": {
                        "name": "HD Monitor",
                        "sku": "HD-MONITOR"
                    },
                    "quantity": 1
                }
            ]
        }

        instance = ImportProductInstance(initial_data, self.import_process)
        instance.process()

        bundle_product = instance.instance
        variation = bundle_product.bundlevariation_through_parents.get(variation__sku="HD-MONITOR")

        self.assertEqual(variation.quantity, 1)

        # Step 2: Re-import with updated quantity
        update_data = {
            "name": "Bundle Monitor Set",
            "sku": "BND-MONITOR",
            "type": Product.BUNDLE,
            "product_type": "Monitor Setup",
            "bundle_variations": [
                {
                    "variation_data": {
                        "name": "HD Monitor",
                        "sku": "HD-MONITOR"
                    },
                    "quantity": 3
                }
            ]
        }

        update_instance = ImportProductInstance(update_data, self.import_process)
        update_instance.process()

        variation.refresh_from_db()
        self.assertEqual(variation.quantity, 3)

    def test_create_product_with_alias_variation(self):
        data = {
            "name": "Main Lamp Product",
            "sku": "LMP-MAIN",
            "type": Product.SIMPLE,
            "product_type": "Lamp",
            "alias_variations": [
                {
                    "variation_data": {
                        "name": "Lamp - Alias",
                        "sku": "LMP-ALIAS"
                    }
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        main = instance.instance
        alias = Product.objects.get(sku="LMP-ALIAS")

        self.assertEqual(alias.type, Product.ALIAS)
        self.assertEqual(alias.alias_parent_product, main)

    def test_create_alias_variation_with_images_copy(self):

        parent_data = {
            "name": "Chair - Original",
            "sku": "CHAIR-ORIGINAL",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "images": [
                {
                    "image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg",
                    "is_main_image": True
                }
            ],
            "alias_variations": [
                {
                    "variation_data": {
                        "name": "Chair - Alias",
                        "sku": "CHAIR-ALIAS"
                    },
                    "alias_copy_images": True
                }
            ]
        }

        instance = ImportProductInstance(parent_data, self.import_process)
        instance.process()

        alias = Product.objects.get(sku="CHAIR-ALIAS")

        self.assertEqual(alias.type, Product.ALIAS)
        self.assertEqual(alias.alias_parent_product.sku, "CHAIR-ORIGINAL")
        self.assertEqual(alias.mediaproductthrough_set.count(), 1)

        media = alias.mediaproductthrough_set.first()
        self.assertTrue(media.is_main_image)

    def test_create_alias_variation_with_property_copy(self):
        data = {
            "name": "Table - Parent",
            "sku": "TABLE-BASE",
            "type": Product.SIMPLE,
            "product_type": "Table",
            "properties": [
                {"property_data": {"name": "Material", "type": "SELECT"}, "value": "Wood"},
                {"property_data": {"name": "Shape", "type": "SELECT"}, "value": "Round"},
            ],
            "alias_variations": [
                {
                    "variation_data": {
                        "name": "Table - Alias",
                        "sku": "TABLE-ALIAS"
                    },
                    "alias_copy_product_properties": True
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        alias = Product.objects.get(sku="TABLE-ALIAS")
        props = ProductProperty.objects.filter(product=alias, property__is_product_type=False)

        self.assertEqual(alias.type, Product.ALIAS)
        self.assertEqual(alias.alias_parent_product.sku, "TABLE-BASE")
        self.assertEqual(props.count(), 2)

        prop_names = set(p.property.name for p in props)
        self.assertSetEqual(prop_names, {"Material", "Shape"})

    def test_alias_variation_with_images_and_properties_copied(self):
        data = {
            "name": "Bed - Base",
            "sku": "BED-BASE",
            "type": Product.SIMPLE,
            "product_type": "Bed",
            "properties": [
                {"property_data": {"name": "Style", "type": "SELECT"}, "value": "Modern"},
            ],
            "images": [
                {"image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg", "is_main_image": True}
            ],
            "alias_variations": [
                {
                    "variation_data": {
                        "name": "Bed - Alias",
                        "sku": "BED-ALIAS"
                    },
                    "alias_copy_images": True,
                    "alias_copy_product_properties": True
                }
            ]
        }

        instance = ImportProductInstance(data, self.import_process)
        instance.process()

        alias = Product.objects.get(sku="BED-ALIAS")

        self.assertEqual(alias.alias_parent_product.sku, "BED-BASE")
        self.assertEqual(alias.mediaproductthrough_set.count(), 1)
        self.assertEqual(ProductProperty.objects.filter(product=alias).exclude(property__is_product_type=True).count(), 1)

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
            "properties": [
                {"property_data": {"name": "Material", "type": "SELECT"}, "value": "Red"},
                {"property_data": {"name": "Style", "type": "SELECT"}, "value": "Elegant"}
            ],
            "images": [
                {"image_url": "https://2.img-dpreview.com/files/p/E~C1000x0S4000x4000T1200x1200~articles/3925134721/0266554465.jpeg"},
                {"image_url": "https://vgl.ucdavis.edu/sites/g/files/dgvnsk15116/files/styles/sf_landscape_4x3/public/images/marketing_highlight/Sample-Collection-Box-Cat-640px.jpg", "is_main_image": True}
            ],
            "prices": [
                {"price": 29.99, "currency": "EUR"},
                {"rrp": 34.99, "currency": "USD"}
            ],
            "configurator_select_values": [
                {"property_data": {"name": "Style", "type": "SELECT"}, "value": "Elegant"}
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
        self.assertTrue(
            MediaProductThrough.objects.get_product_images(
                product=instance.instance,
                sales_channel=None,
            ).exists()
        )
        self.assertTrue(SalesPrice.objects.filter(product=instance.instance).count() >= 2)
        self.assertTrue(ConfigurableVariation.objects.filter(parent=instance.instance).exists())
        self.assertTrue(ProductPropertiesRuleItem.objects.filter(rule=instance.rule).count() >= 2)
        self.assertTrue(ProductProperty.objects.filter(product=instance.instance).count() >= 1)


class ImportProductInstanceParentLinkingTest(TestCase):
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

    def test_link_simple_to_configurable_parent(self):
        parent_data = {
            "name": "Configurable Product",
            "sku": "CFG-001",
            "type": Product.CONFIGURABLE,
            "product_type": "Chair",
        }
        ImportProductInstance(parent_data, self.import_process).process()

        child_data = {
            "name": "Variant A",
            "sku": "VAR-001",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "configurable_parent_sku": "CFG-001"
        }
        ImportProductInstance(child_data, self.import_process).process()

        link = ConfigurableVariation.objects.filter(parent__sku="CFG-001", variation__sku="VAR-001").first()
        self.assertIsNotNone(link)

    def test_link_simple_to_configurable_parent_from_plural_field(self):
        parent_data = {
            "name": "Configurable Product",
            "sku": "CFG-001",
            "type": Product.CONFIGURABLE,
            "product_type": "Chair",
        }
        ImportProductInstance(parent_data, self.import_process).process()

        child_data = {
            "name": "Variant B",
            "sku": "VAR-002",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "configurable_parent_skus": ["CFG-UNKNOWN", "CFG-001"],
        }
        ImportProductInstance(child_data, self.import_process).process()

        link = ConfigurableVariation.objects.filter(parent__sku="CFG-001", variation__sku="VAR-002").first()
        self.assertIsNotNone(link)

    def test_link_simple_to_bundle_parent(self):
        parent_data = {
            "name": "Bundle Base",
            "sku": "BND-001",
            "type": Product.BUNDLE,
            "product_type": "Chair",
        }
        ImportProductInstance(parent_data, self.import_process).process()

        child_data = {
            "name": "Bundle Item",
            "sku": "ITM-001",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "bundle_parent_sku": "BND-001"
        }
        ImportProductInstance(child_data, self.import_process).process()

        link = BundleVariation.objects.filter(parent__sku="BND-001", variation__sku="ITM-001").first()
        self.assertIsNotNone(link)
        self.assertEqual(link.quantity, 1)

    def test_link_simple_to_bundle_parent_from_plural_field(self):
        parent_data = {
            "name": "Bundle Base",
            "sku": "BND-001",
            "type": Product.BUNDLE,
            "product_type": "Chair",
        }
        ImportProductInstance(parent_data, self.import_process).process()

        child_data = {
            "name": "Bundle Item",
            "sku": "ITM-002",
            "type": Product.SIMPLE,
            "product_type": "Chair",
            "bundle_parent_skus": ["BND-UNKNOWN", "BND-001"],
        }
        ImportProductInstance(child_data, self.import_process).process()

        link = BundleVariation.objects.filter(parent__sku="BND-001", variation__sku="ITM-002").first()
        self.assertIsNotNone(link)

    def test_link_alias_to_parent_using_sku(self):
        parent_data = {
            "name": "Main Product",
            "sku": "MAIN-001",
            "type": Product.SIMPLE,
            "product_type": "Chair",
        }
        ImportProductInstance(parent_data, self.import_process).process()

        alias_data = {
            "name": "Alias Product",
            "sku": "ALIAS-001",
            "type": Product.ALIAS,
            "product_type": "Chair",
            "alias_parent_sku": "MAIN-001"
        }
        ImportProductInstance(alias_data, self.import_process).process()

        alias = Product.objects.get(sku="ALIAS-001")
        self.assertIsNotNone(alias.alias_parent_product)
        self.assertEqual(alias.alias_parent_product.sku, "MAIN-001")


class ImportProductInstanceCreateOnlyTest(TestCase):
    def setUp(self):
        super().setUp()
        self.initial_import = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.create_only_import = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            create_only=True,
        )

    def test_existing_product_not_updated_when_create_only(self):
        import base64

        first_data = {
            "name": "Original Product",
            "sku": "CO-001",
            "images": [
                {"image_content": base64.b64encode(b"img1").decode("utf-8"), "is_main_image": True}
            ],
        }
        instance1 = ImportProductInstance(first_data, self.initial_import)
        instance1.process()
        product = instance1.instance
        self.assertEqual(product.name, "Original Product")
        initial_images = MediaProductThrough.objects.get_product_images(
            product=product,
            sales_channel=None,
        ).count()

        second_data = {
            "name": "Updated Product",
            "sku": "CO-001",
            "images": [
                {"image_content": base64.b64encode(b"img2").decode("utf-8")}
            ],
        }
        instance2 = ImportProductInstance(second_data, self.create_only_import)
        instance2.process()

        product.refresh_from_db()
        self.assertEqual(product.name, "Original Product")
        self.assertEqual(
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=None,
            ).count(),
            initial_images,
        )

    def test_existing_product_updated_when_not_create_only(self):
        import base64

        first_data = {
            "name": "Original Product",
            "sku": "CO-001",
            "images": [
                {"image_content": base64.b64encode(b"img1").decode("utf-8"), "is_main_image": True}
            ],
        }
        instance1 = ImportProductInstance(first_data, self.initial_import)
        instance1.process()
        product = instance1.instance
        self.assertEqual(product.name, "Original Product")
        initial_images = MediaProductThrough.objects.get_product_images(
            product=product,
            sales_channel=None,
        ).count()

        second_data = {
            "name": "Updated Product",
            "sku": "CO-001",
            "images": [
                {"image_content": base64.b64encode(b"img2").decode("utf-8")}
            ],
        }
        # create_only=False import
        update_import = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            create_only=False,
        )
        instance2 = ImportProductInstance(second_data, update_import)
        instance2.process()

        product.refresh_from_db()
        self.assertEqual(product.name, "Updated Product")
        self.assertEqual(
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=None,
            ).count(),
            initial_images + 1,
        )


class ImportProductInstanceUpdateOnlyTest(TestCase):
    def setUp(self):
        super().setUp()
        self.initial_import = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.update_only_import = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            update_only=True,
        )

    def test_existing_product_updated_when_update_only(self):
        first_data = {
            "name": "Original Product",
            "sku": "UO-001",
        }
        ImportProductInstance(first_data, self.initial_import).process()

        second_data = {
            "name": "Updated Product",
            "sku": "UO-001",
        }
        ImportProductInstance(second_data, self.update_only_import).process()

        product = Product.objects.get(sku="UO-001")
        self.assertEqual(product.name, "Updated Product")

    def test_missing_product_raises_error_when_update_only(self):
        data = {
            "name": "New Product",
            "sku": "UO-002",
        }
        instance = ImportProductInstance(data, self.update_only_import)
        with self.assertRaises(UpdateOnlyInstanceNotFound):
            instance.process()


class ImportProductWithSameSkuAndDifferentTypeTest(TestCase):
    def setUp(self):
        super().setUp()
        self.import_instance = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_fallback_applies_when_type_is_wrong(self):
        first_data = {
            "name": "First",
            "sku": "FALLBACK-001",
            "type": "SIMPLE"
        }
        instance1 = ImportProductInstance(first_data, self.import_instance)
        instance1.process()
        product = instance1.instance

        # Second time with wrong type
        second_data = {
            "name": "Second Attempt",
            "sku": "FALLBACK-001",
            "type": "BUNDLE"
        }

        instance2 = ImportProductInstance(second_data, self.import_instance)
        instance2.process()

        self.assertEqual(instance2.instance.id, product.id)
        self.assertEqual(instance2.created, False)
        self.assertEqual(instance2.instance.type, product.type)
        self.assertEqual(instance2.instance.type, "SIMPLE")
