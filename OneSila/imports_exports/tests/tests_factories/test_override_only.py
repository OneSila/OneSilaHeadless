import base64
from datetime import date, datetime
from decimal import Decimal

from model_bakery import baker

from core.tests import TestCase
from unittest.mock import patch
from eancodes.models import EanCode
from imports_exports.factories.products import ImportProductInstance
from imports_exports.models import Import
from media.models import Media, MediaProductThrough
from products.models import Product, ProductTranslation, ConfigurableVariation
from properties.models import Property, ProductProperty
from properties.models import PropertySelectValue, ProductPropertiesRule, ProductPropertyTextTranslation
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from taxes.models import VatRate


class ImportOverrideOnlyProductTests(TestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._populate_media_title_patcher = patch(
            "media.tasks.populate_media_title_task",
            return_value=None,
        )
        self._populate_media_title_patcher.start()
        self.addCleanup(self._populate_media_title_patcher.stop)

        self._salespricelistitem_update_prices_patcher = patch(
            "sales_prices.tasks.salespricelistitem__update_prices_task",
            return_value=None,
        )
        self._salespricelistitem_update_prices_patcher.start()
        self.addCleanup(self._salespricelistitem_update_prices_patcher.stop)

        self.override_only_import = Import.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            override_only=True,
        )

    def test_existing_fields_not_overridden(self, *, _unused=None):
        vat_rate_current = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rate=19,
        )
        vat_rate_new = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rate=7,
        )
        product = baker.make(
            Product,
            sku="OVR-001",
            type=Product.SIMPLE,
            active=False,
            allow_backorder=False,
            vat_rate=vat_rate_current,
            multi_tenant_company=self.multi_tenant_company,
        )

        data = {
            "sku": "OVR-001",
            "type": Product.SIMPLE,
            "active": True,
            "allow_backorder": True,
            "vat_rate": vat_rate_new.rate,
        }
        ImportProductInstance(data, self.override_only_import).process()

        product.refresh_from_db()
        self.assertFalse(product.active)
        self.assertFalse(product.allow_backorder)
        self.assertEqual(product.vat_rate_id, vat_rate_current.id)

    def test_missing_vat_rate_is_set(self, *, _unused=None):
        vat_rate_new = VatRate.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            rate=21,
        )
        product = baker.make(
            Product,
            sku="OVR-002",
            type=Product.SIMPLE,
            vat_rate=None,
            multi_tenant_company=self.multi_tenant_company,
        )

        data = {
            "sku": "OVR-002",
            "type": Product.SIMPLE,
            "vat_rate": vat_rate_new.rate,
        }
        ImportProductInstance(data, self.override_only_import).process()

        product.refresh_from_db()
        self.assertEqual(product.vat_rate_id, vat_rate_new.id)

    def test_existing_ean_code_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-003",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            ean_code="1111111111111",
            already_used=True,
            internal=False,
        )

        data = {
            "sku": "OVR-003",
            "type": Product.SIMPLE,
            "ean_code": "2222222222222",
        }
        ImportProductInstance(data, self.override_only_import).process()

        ean_codes = EanCode.objects.filter(product=product)
        self.assertEqual(ean_codes.count(), 1)
        self.assertEqual(ean_codes.first().ean_code, "1111111111111")

    def test_product_property_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-004",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        types = [
            Property.TYPES.INT,
            Property.TYPES.FLOAT,
            Property.TYPES.BOOLEAN,
            Property.TYPES.DATE,
            Property.TYPES.DATETIME,
            Property.TYPES.TEXT,
            Property.TYPES.DESCRIPTION,
            Property.TYPES.SELECT,
            Property.TYPES.MULTISELECT,
        ]

        for index, prop_type in enumerate(types, start=1):
            prop = baker.make(
                Property,
                type=prop_type,
                multi_tenant_company=self.multi_tenant_company,
            )
            product_property = ProductProperty.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                property=prop,
            )
            if prop_type == Property.TYPES.INT:
                product_property.value_int = 5
            elif prop_type == Property.TYPES.FLOAT:
                product_property.value_float = 1.5
            elif prop_type == Property.TYPES.BOOLEAN:
                product_property.value_boolean = True
            elif prop_type == Property.TYPES.DATE:
                product_property.value_date = date(2024, 1, 1)
            elif prop_type == Property.TYPES.DATETIME:
                product_property.value_datetime = datetime(2024, 1, 1, 10, 0, 0)
            elif prop_type == Property.TYPES.TEXT:
                ProductPropertyTextTranslation.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product_property=product_property,
                    language=self.multi_tenant_company.language,
                    value_text="Original text",
                )
            elif prop_type == Property.TYPES.DESCRIPTION:
                ProductPropertyTextTranslation.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    product_property=product_property,
                    language=self.multi_tenant_company.language,
                    value_description="Original description",
                )
            elif prop_type == Property.TYPES.SELECT:
                select_value = PropertySelectValue.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    property=prop,
                )
                product_property.value_select = select_value
            elif prop_type == Property.TYPES.MULTISELECT:
                value_one = PropertySelectValue.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    property=prop,
                )
                value_two = PropertySelectValue.objects.create(
                    multi_tenant_company=self.multi_tenant_company,
                    property=prop,
                )
                product_property.save()
                product_property.value_multi_select.set([value_one])
            product_property.save()

            if prop_type == Property.TYPES.INT:
                new_value = 10
            elif prop_type == Property.TYPES.FLOAT:
                new_value = 1.6
            elif prop_type == Property.TYPES.BOOLEAN:
                new_value = False
            elif prop_type == Property.TYPES.DATE:
                new_value = "2024-02-01"
            elif prop_type == Property.TYPES.DATETIME:
                new_value = "2024-02-01 12:00:00"
            elif prop_type == Property.TYPES.TEXT:
                new_value = "Updated text"
            elif prop_type == Property.TYPES.DESCRIPTION:
                new_value = "Updated description"
            elif prop_type == Property.TYPES.SELECT:
                new_value = "Updated select"
            else:
                new_value = ["Updated select"]

            data = {
                "sku": f"OVR-004-{index}",
                "type": Product.SIMPLE,
                "properties": [{"property": prop, "value": new_value}],
            }
            product.sku = data["sku"]
            product.save()

            with self.subTest(prop_type=prop_type):
                ImportProductInstance(data, self.override_only_import).process()

                product_property.refresh_from_db()
                if prop_type == Property.TYPES.INT:
                    self.assertEqual(product_property.value_int, 5)
                elif prop_type == Property.TYPES.FLOAT:
                    self.assertEqual(product_property.value_float, 1.5)
                elif prop_type == Property.TYPES.BOOLEAN:
                    self.assertTrue(product_property.value_boolean)
                elif prop_type == Property.TYPES.DATE:
                    self.assertEqual(str(product_property.value_date), "2024-01-01")
                elif prop_type == Property.TYPES.DATETIME:
                    self.assertEqual(
                        product_property.value_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        "2024-01-01 10:00:00",
                    )
                elif prop_type == Property.TYPES.TEXT:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=product_property,
                        language=self.multi_tenant_company.language,
                    )
                    self.assertEqual(translation.value_text, "Original text")
                elif prop_type == Property.TYPES.DESCRIPTION:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=product_property,
                        language=self.multi_tenant_company.language,
                    )
                    self.assertEqual(translation.value_description, "Original description")
                elif prop_type == Property.TYPES.SELECT:
                    self.assertEqual(product_property.value_select_id, select_value.id)
                else:
                    self.assertEqual(list(product_property.value_multi_select.values_list("id", flat=True)), [value_one.id])

    def test_product_property_created_when_missing(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-005",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        types = [
            Property.TYPES.INT,
            Property.TYPES.FLOAT,
            Property.TYPES.BOOLEAN,
            Property.TYPES.DATE,
            Property.TYPES.DATETIME,
            Property.TYPES.TEXT,
            Property.TYPES.DESCRIPTION,
            Property.TYPES.SELECT,
            Property.TYPES.MULTISELECT,
        ]

        for index, prop_type in enumerate(types, start=1):
            prop = baker.make(
                Property,
                type=prop_type,
                multi_tenant_company=self.multi_tenant_company,
            )

            if prop_type == Property.TYPES.INT:
                new_value = 10
            elif prop_type == Property.TYPES.FLOAT:
                new_value = 1.6
            elif prop_type == Property.TYPES.BOOLEAN:
                new_value = True
            elif prop_type == Property.TYPES.DATE:
                new_value = "2024-02-01"
            elif prop_type == Property.TYPES.DATETIME:
                new_value = "2024-02-01 12:00:00"
            elif prop_type == Property.TYPES.TEXT:
                new_value = "Created text"
            elif prop_type == Property.TYPES.DESCRIPTION:
                new_value = "Created description"
            elif prop_type == Property.TYPES.SELECT:
                new_value = "Created select"
            else:
                new_value = ["Created select"]

            data = {
                "sku": f"OVR-005-{index}",
                "type": Product.SIMPLE,
                "properties": [{"property": prop, "value": new_value}],
            }
            product.sku = data["sku"]
            product.save()

            with self.subTest(prop_type=prop_type):
                ImportProductInstance(data, self.override_only_import).process()

                product_property = ProductProperty.objects.get(product=product, property=prop)
                if prop_type == Property.TYPES.INT:
                    self.assertEqual(product_property.value_int, 10)
                elif prop_type == Property.TYPES.FLOAT:
                    self.assertEqual(product_property.value_float, 1.6)
                elif prop_type == Property.TYPES.BOOLEAN:
                    self.assertTrue(product_property.value_boolean)
                elif prop_type == Property.TYPES.DATE:
                    self.assertEqual(str(product_property.value_date), "2024-02-01")
                elif prop_type == Property.TYPES.DATETIME:
                    self.assertEqual(
                        product_property.value_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        "2024-02-01 12:00:00",
                    )
                elif prop_type == Property.TYPES.TEXT:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=product_property,
                        language=self.multi_tenant_company.language,
                    )
                    self.assertEqual(translation.value_text, "Created text")
                elif prop_type == Property.TYPES.DESCRIPTION:
                    translation = ProductPropertyTextTranslation.objects.get(
                        product_property=product_property,
                        language=self.multi_tenant_company.language,
                    )
                    self.assertEqual(translation.value_description, "Created description")
                elif prop_type == Property.TYPES.SELECT:
                    self.assertIsNotNone(product_property.value_select_id)
                else:
                    self.assertEqual(product_property.value_multi_select.count(), 1)

    def test_prices_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-006",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            currency=self.currency,
            price=Decimal("10.00"),
        )

        data = {
            "sku": "OVR-006",
            "type": Product.SIMPLE,
            "prices": [{"currency": self.currency.iso_code, "price": Decimal("20.00")}],
        }
        ImportProductInstance(data, self.override_only_import).process()

        price = SalesPrice.objects.get(product=product, currency=self.currency)
        self.assertEqual(price.price, Decimal("10.00"))

    def test_images_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-007",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        image = baker.make(
            Media,
            type=Media.IMAGE,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            media=image,
        )

        data = {
            "sku": "OVR-007",
            "type": Product.SIMPLE,
            "images": [{"image_content": base64.b64encode(b"img1").decode("utf-8")}],
        }
        ImportProductInstance(data, self.override_only_import).process()

        self.assertEqual(
            MediaProductThrough.objects.filter(product=product, sales_channel__isnull=True).count(),
            1,
        )

    def test_images_created_when_missing(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-008",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )

        data = {
            "sku": "OVR-008",
            "type": Product.SIMPLE,
            "images": [{"image_content": base64.b64encode(b"img2").decode("utf-8")}],
        }
        ImportProductInstance(data, self.override_only_import).process()

        self.assertEqual(
            MediaProductThrough.objects.filter(product=product, sales_channel__isnull=True).count(),
            1,
        )

    def test_translations_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-009",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name="Original",
            description="Old description",
        )

        data = {
            "sku": "OVR-009",
            "type": Product.SIMPLE,
            "translations": [
                {
                    "language": self.multi_tenant_company.language,
                    "name": "Updated",
                    "description": "New description",
                }
            ],
        }
        ImportProductInstance(data, self.override_only_import).process()

        translation = ProductTranslation.objects.get(product=product, sales_channel__isnull=True)
        self.assertEqual(translation.name, "Original")
        self.assertEqual(translation.description, "Old description")

    def test_translation_missing_value_updates(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-010",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name="Original",
            description=None,
        )

        data = {
            "sku": "OVR-010",
            "type": Product.SIMPLE,
            "translations": [
                {
                    "language": self.multi_tenant_company.language,
                    "name": "Original",
                    "description": "Filled description",
                }
            ],
        }
        ImportProductInstance(data, self.override_only_import).process()

        translation = ProductTranslation.objects.get(product=product, sales_channel__isnull=True)
        self.assertEqual(translation.description, "Filled description")

    def test_sales_pricelist_items_not_overridden(self, *, _unused=None):
        product = baker.make(
            Product,
            sku="OVR-011",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        price_list = SalesPriceList.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Retail",
            currency=self.currency,
        )
        item = SalesPriceListItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            salespricelist=price_list,
            product=product,
            price_override=Decimal("10.00"),
        )

        data = {
            "sku": "OVR-011",
            "type": Product.SIMPLE,
            "sales_pricelist_items": [
                {"salespricelist": price_list, "price_override": Decimal("20.00")}
            ],
        }
        ImportProductInstance(data, self.override_only_import).process()

        item.refresh_from_db()
        self.assertEqual(item.price_override, Decimal("10.00"))

    def test_product_type_not_overridden(self, *, _unused=None):
        product_type_property =  Property.objects.get(
            type=Property.TYPES.SELECT,
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        current_type = baker.make(
            PropertySelectValue,
            property=product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        new_type = baker.make(
            PropertySelectValue,
            property=product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        current_rule = ProductPropertiesRule.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product_type=current_type,
            sales_channel=None,
        )
        new_rule = ProductPropertiesRule.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            product_type=new_type,
            sales_channel=None,
        )
        product = baker.make(
            Product,
            sku="OVR-013",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=product_type_property,
            value_select=current_rule.product_type,
        )

        data = {
            "sku": "OVR-013",
            "type": Product.SIMPLE,
        }
        ImportProductInstance(
            data,
            self.override_only_import,
            instance=product,
            rule=new_rule,
            update_current_rule=True,
        ).process()

        product_type_property = ProductProperty.objects.get(
            product=product,
            property=product_type_property,
        )
        self.assertEqual(product_type_property.value_select_id, current_rule.product_type_id)

    def test_configurable_variations_not_overridden(self, *, _unused=None):
        parent = baker.make(
            Product,
            sku="OVR-012",
            type=Product.CONFIGURABLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        variation = baker.make(
            Product,
            sku="OVR-012-V1",
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=parent,
            variation=variation,
        )

        data = {
            "sku": "OVR-012",
            "type": Product.CONFIGURABLE,
            "variations": [],
        }
        ImportProductInstance(data, self.override_only_import, instance=parent).process()

        self.assertEqual(
            ConfigurableVariation.objects.filter(parent=parent).count(),
            1,
        )
