from unittest.mock import patch

from core.tests import TestCase
from imports_exports.models import Import
from model_bakery import baker
from properties.models import (
    ProductProperty,
    ProductPropertiesRule,
    Property,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductsImportProcessor
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonProductType,
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonImportData,
)


class AmazonProductsImportProcessorNameTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER"
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_name_from_attributes(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Attr name"}]},
            "summaries": [{
                "item_name": "Summary name",
                "asin": "ASIN",
                "marketplace_id": "GB",
                "status": ["BUYABLE"],
                "product_type": "TYPE",
            }],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None), \
                patch.object(AmazonProductsImportProcessor, "_parse_images", return_value=[]), \
                patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=([], [])), \
                patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
                patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)
        self.assertEqual(structured["name"], "Attr name")

    def test_name_fallback_to_summary(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {},
            "summaries": [{
                "item_name": "Summary name",
                "asin": "ASIN",
                "marketplace_id": "GB",
                "status": ["BUYABLE"],
                "product_type": "TYPE",
            }],
        }
        with patch.object(AmazonProductsImportProcessor, "get_api", return_value=None), \
                patch.object(AmazonProductsImportProcessor, "_parse_images", return_value=[]), \
                patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=([], [])), \
                patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
                patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)
        self.assertEqual(structured["name"], "Summary name")


class AmazonProductsImportProcessorPriceTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

    def test_missing_currency_raises_error(self):
        product_data = {
            "offers": [
                {"offer_type": "B2C", "price": {"amount": "10", "currency_code": "USD"}}
            ]
        }
        processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
        with self.assertRaises(ValueError):
            processor._parse_prices(product_data)

    def test_currency_object_in_salespricelist_data(self):
        product_data = {
            "offers": [
                {"offer_type": "B2C", "price": {"amount": "10", "currency_code": "GBP"}}
            ]
        }
        processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
        _, items = processor._parse_prices(product_data)
        self.assertEqual(
            items[0]["salespricelist_data"]["currency_object"], self.currency
        )


class AmazonProductsImportProcessorRulePreserveTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)

        # create product type and rule
        self.product_type_property, _ = Property.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            type=Property.TYPES.SELECT,
        )
        self.product_type_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=self.product_type_property,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
            value="Default",
        )
        self.rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=self.product_type_value,
        )

        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product_type_code="DEFAULT_CODE",
            local_instance=self.rule,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_sku="SKU123",
            local_instance=self.product,
            is_variation=False,
        )

    def test_rule_kept_when_product_type_mismatch(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Name"}]},
            "summaries": [
                {
                    "item_name": "Name",
                    "asin": "ASIN1",
                    "marketplace_id": "GB",
                    "status": ["BUYABLE"],
                    "product_type": "OTHER_CODE",
                }
            ],
        }

        structured = {"name": "Name", "sku": "SKU123", "__asin": "ASIN1", "type": "SIMPLE"}

        with patch.object(AmazonProductsImportProcessor, "get__product_data", return_value=(structured, None, self.view)), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.ImportProductInstance") as MockImportProductInstance, \
                patch.object(AmazonProductsImportProcessor, "update_remote_product"), \
                patch.object(AmazonProductsImportProcessor, "handle_ean_code"), \
                patch.object(AmazonProductsImportProcessor, "handle_attributes"), \
                patch.object(AmazonProductsImportProcessor, "handle_translations"), \
                patch.object(AmazonProductsImportProcessor, "handle_prices"), \
                patch.object(AmazonProductsImportProcessor, "handle_images"), \
                patch.object(AmazonProductsImportProcessor, "handle_variations"), \
                patch.object(AmazonProductsImportProcessor, "handle_sales_channels_views"), \
                patch.object(AmazonProductsImportProcessor, "_add_broken_record") as mock_broken, \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.FetchRemoteIssuesFactory") as MockIssuesFactory:

            from types import SimpleNamespace

            mock_instance = SimpleNamespace(
                process=lambda: None,
                prepare_mirror_model_class=lambda *args, **kwargs: None,
                remote_instance=self.remote_product,
            )
            MockImportProductInstance.return_value = mock_instance
            MockIssuesFactory.return_value.run.return_value = None

            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            processor.process_product_item(product_data)

            called_rule = MockImportProductInstance.call_args.kwargs["rule"]
            self.assertEqual(called_rule, self.rule)
            self.assertTrue(mock_broken.called)


class AmazonProductsImportProcessorImportDataTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.import_process = Import.objects.create(multi_tenant_company=self.multi_tenant_company)
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )

    def test_import_data_saved(self):
        product_data = {
            "sku": "SKU123",
            "attributes": {"item_name": [{"value": "Name"}]},
            "summaries": [
                {
                    "item_name": "Name",
                    "asin": "ASIN1",
                    "marketplace_id": "GB",
                    "status": ["BUYABLE"],
                    "product_type": "TYPE",
                }
            ],
        }

        structured = {"name": "Name", "sku": "SKU123", "__asin": "ASIN1", "type": "SIMPLE"}

        with patch.object(AmazonProductsImportProcessor, "get__product_data", return_value=(structured, None, self.view)), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.ImportProductInstance") as MockImportProductInstance, \
                patch.object(AmazonProductsImportProcessor, "update_remote_product"), \
                patch.object(AmazonProductsImportProcessor, "handle_ean_code"), \
                patch.object(AmazonProductsImportProcessor, "handle_attributes"), \
                patch.object(AmazonProductsImportProcessor, "handle_translations"), \
                patch.object(AmazonProductsImportProcessor, "handle_prices"), \
                patch.object(AmazonProductsImportProcessor, "handle_images"), \
                patch.object(AmazonProductsImportProcessor, "handle_variations"), \
                patch.object(AmazonProductsImportProcessor, "handle_sales_channels_views"), \
                patch("sales_channels.integrations.amazon.factories.imports.products_imports.FetchRemoteIssuesFactory") as MockIssuesFactory:

            from types import SimpleNamespace

            mock_instance = SimpleNamespace(
                process=lambda: None,
                prepare_mirror_model_class=lambda *args, **kwargs: None,
                local_instance=self.product,
                remote_instance=None,
            )
            MockImportProductInstance.return_value = mock_instance
            MockIssuesFactory.return_value.run.return_value = None

            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            processor.process_product_item(product_data)

        saved = AmazonImportData.objects.get()
        self.assertEqual(saved.sales_channel, self.sales_channel)
        self.assertEqual(saved.product, self.product)
        self.assertEqual(saved.view, self.view)
        self.assertEqual(saved.data["sku"], "SKU123")
