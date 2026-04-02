from unittest.mock import patch

from core.tests import TestCase
from eancodes.models import EanCode
from imports_exports.models import Export
from products.models import (
    ConfigurableVariation,
    Product,
    ProductTranslation,
    ProductTranslationBulletPoint,
)
from properties.models import ProductProperty, Property, PropertySelectValue, PropertySelectValueTranslation, PropertyTranslation
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.models import SalesChannelViewAssign


class ExportModelTest(TestCase):
    @patch("imports_exports.models.safe_run_task")
    def test_str_with_name(self, mocked_safe_run_task):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="My Export",
            kind=Export.KIND_PROPERTIES,
        )

        self.assertEqual(str(export_process), "My Export - New (0%)")
        mocked_safe_run_task.assert_not_called()

    @patch("imports_exports.models.safe_run_task")
    def test_pending_export_queues_task_on_create(self, mocked_safe_run_task):
        Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            status=Export.STATUS_PENDING,
        )

        mocked_safe_run_task.assert_called_once()

    @patch("imports_exports.models.safe_run_task")
    def test_periodic_non_feed_validation(self, mocked_safe_run_task):
        export_process = Export(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            type=Export.TYPE_JSON,
            is_periodic=True,
        )

        with self.assertRaisesMessage(Exception, "Periodic exports are only supported for json_feed exports."):
            export_process.clean()

        mocked_safe_run_task.assert_not_called()

    @patch("imports_exports.models.safe_run_task")
    def test_run_async_dispatches_task(self, mocked_safe_run_task):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
        )

        export_process.run(run_async=True)

        mocked_safe_run_task.assert_called_once()


class ExportRunnerTest(TestCase):
    def setUp(self):
        super().setUp()
        self.property = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="color",
            type=Property.TYPES.SELECT,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.property,
            language=self.multi_tenant_company.language,
            name="Color",
        )
        self.select_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.property,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.select_value,
            language=self.multi_tenant_company.language,
            value="Red",
        )

        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="EXPORT-001",
            type=Product.SIMPLE,
            active=True,
        )
        self.default_translation = ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Export Product",
            subtitle="Default Subtitle",
            short_description="Short",
            description="Long",
        )
        ProductTranslationBulletPoint.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_translation=self.default_translation,
            text="Default bullet",
            sort_order=0,
        )
        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://amazon.example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.sales_channel_view = AmazonSalesChannelView.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.channel_translation = ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            language=self.multi_tenant_company.language,
            sales_channel=self.sales_channel,
            name="Amazon Export Product",
            subtitle="Amazon Subtitle",
            short_description="Amazon Short",
            description="Amazon Long",
        )
        ProductTranslationBulletPoint.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_translation=self.channel_translation,
            text="Amazon bullet",
            sort_order=0,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.sales_channel_view,
        )

        self.configurable_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="CONFIG-001",
            type=Product.CONFIGURABLE,
            active=True,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.configurable_product,
            language=self.multi_tenant_company.language,
            name="Configurable Product",
        )
        self.variation_product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sku="VAR-001",
            type=Product.SIMPLE,
            active=True,
        )
        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.variation_product,
            language=self.multi_tenant_company.language,
            name="Variation Product",
        )
        ConfigurableVariation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            parent=self.configurable_product,
            variation=self.variation_product,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.configurable_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.sales_channel_view,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=self.property,
            value_select=self.select_value,
        )
        self.ean_code = EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )

    def test_json_export_generates_import_compatible_raw_data(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PRODUCTS,
            type=Export.TYPE_JSON,
            columns=["sku", "translations", "properties"],
            parameters={"product_properties": {"add_value_ids": True}},
        )

        export_process.run()
        export_process.refresh_from_db()


        self.assertEqual(export_process.status, Export.STATUS_SUCCESS)
        self.assertTrue(export_process.file.name.endswith(".json"))
        self.assertEqual(export_process.raw_data[0]["sku"], "EXPORT-001")
        self.assertEqual(export_process.raw_data[0]["properties"][0]["value"], self.select_value.id)
        self.assertEqual(export_process.raw_data[0]["properties"][0]["values"][0]["value"], self.select_value.id)
        self.assertEqual(export_process.raw_data[0]["translations"][0]["name"], "Export Product")

    def test_product_export_includes_all_translations_and_sales_channels(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PRODUCTS,
            type=Export.TYPE_JSON,
            columns=["sku", "translations", "sales_channels"],
            parameters={"product_ids": [self.product.id, self.variation_product.id]},
        )

        export_process.run()
        export_process.refresh_from_db()

        rows_by_sku = {
            row["sku"]: row
            for row in export_process.raw_data
        }

        exported_product = rows_by_sku["EXPORT-001"]
        translations_by_sales_channel_id = {
            translation["sales_channel"]: translation
            for translation in exported_product["translations"]
        }
        self.assertIn(None, translations_by_sales_channel_id)
        self.assertIn(self.sales_channel.id, translations_by_sales_channel_id)
        self.assertEqual(translations_by_sales_channel_id[None]["subtitle"], "Default Subtitle")
        self.assertEqual(
            translations_by_sales_channel_id[self.sales_channel.id]["subtitle"],
            "Amazon Subtitle",
        )
        self.assertEqual(
            translations_by_sales_channel_id[self.sales_channel.id]["bullet_points"],
            ["Amazon bullet"],
        )
        self.assertEqual(
            exported_product["sales_channels"],
            [
                {
                    "id": self.sales_channel.id,
                    "hostname": "https://amazon.example.com",
                    "type": "amazon",
                    "subtype": None,
                },
            ],
        )

        exported_variation = rows_by_sku["VAR-001"]
        self.assertEqual(
            exported_variation["sales_channels"],
            [
                {
                    "id": self.sales_channel.id,
                    "hostname": "https://amazon.example.com",
                    "type": "amazon",
                    "subtype": None,
                },
            ],
        )

    def test_export_sets_total_records_from_queryset_and_updates_progress(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PRODUCTS,
            type=Export.TYPE_JSON,
            columns=["sku"],
        )

        original_save = export_process.save
        recorded_percentages = []

        def tracked_save(*args, **kwargs):
            update_fields = tuple(kwargs.get("update_fields") or ())
            if "percentage" in update_fields:
                recorded_percentages.append(export_process.percentage)
            return original_save(*args, **kwargs)

        with patch.object(export_process, "save", side_effect=tracked_save):
            export_process.run()

        export_process.refresh_from_db()

        self.assertEqual(export_process.total_records, 3)
        self.assertEqual(len(export_process.raw_data), 3)
        self.assertIn(30, recorded_percentages)
        self.assertIn(60, recorded_percentages)
        self.assertIn(90, recorded_percentages)

    def test_ean_codes_export_is_simple_import_compatible_payload(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_EAN_CODES,
            type=Export.TYPE_JSON,
        )

        export_process.run()
        export_process.refresh_from_db()

        self.assertEqual(
            export_process.raw_data,
            [
                {
                    "ean_code": "1234567890123",
                    "product_sku": "EXPORT-001",
                }
            ],
        )

    def test_csv_export_preserves_raw_data_before_failure(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            type=Export.TYPE_CSV,
            columns=["name"],
        )

        export_process.run()
        export_process.refresh_from_db()

        self.assertEqual(export_process.status, Export.STATUS_FAILED)
        self.assertTrue(export_process.raw_data)
        self.assertIn("CSV file generation is not implemented yet", export_process.error_traceback)

    def test_no_columns_defaults_to_all_supported_columns(self):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PRODUCTS,
            type=Export.TYPE_JSON,
            columns=[],
            parameters={"flat": True},
        )

        export_process.run()
        export_process.refresh_from_db()

        row = export_process.raw_data[0]
        self.assertIn("sku", row)
        self.assertIn("translations", row)
        self.assertIn("sales_channels", row)
        self.assertIn("configurable_products_skus", row)
        self.assertIn("bundle_products_skus", row)
        self.assertIn("alias_products_skus", row)


class DirectExportFeedViewTest(TestCase):
    @patch("imports_exports.models.safe_run_task")
    def test_direct_feed_requires_bearer_token(self, mocked_safe_run_task):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            type=Export.TYPE_JSON_FEED,
            status=Export.STATUS_SUCCESS,
            raw_data={"hello": "world"},
        )

        response = self.client.get(f"/direct/export/{export_process.feed_key}/")
        self.assertEqual(response.status_code, 403)
        mocked_safe_run_task.assert_not_called()

    @patch("imports_exports.models.safe_run_task")
    def test_direct_feed_returns_json(self, mocked_safe_run_task):
        export_process = Export.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            kind=Export.KIND_PROPERTIES,
            type=Export.TYPE_JSON_FEED,
            status=Export.STATUS_SUCCESS,
            raw_data={"hello": "world"},
        )

        response = self.client.get(
            f"/direct/export/{export_process.feed_key}/",
            HTTP_AUTHORIZATION="Bearer anything",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"hello": "world"})
        mocked_safe_run_task.assert_not_called()
