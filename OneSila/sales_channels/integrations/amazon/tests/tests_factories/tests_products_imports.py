from unittest.mock import patch

from core.tests import TestCase
from imports_exports.models import Import
from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductsImportProcessor
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView


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
             patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=[]), \
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
             patch.object(AmazonProductsImportProcessor, "_parse_prices", return_value=[]), \
             patch.object(AmazonProductsImportProcessor, "_parse_attributes", return_value=([], {})), \
             patch.object(AmazonProductsImportProcessor, "_fetch_catalog_attributes", return_value=None):
            processor = AmazonProductsImportProcessor(self.import_process, self.sales_channel)
            structured, _, _ = processor.get__product_data(product_data, False)
        self.assertEqual(structured["name"], "Summary name")
