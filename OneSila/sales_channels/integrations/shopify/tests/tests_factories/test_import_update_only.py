from unittest.mock import MagicMock, patch

from core.tests import TransactionTestCase
from products.models import Product
from sales_channels.integrations.shopify.factories.imports.imports import ShopifyImportProcessor
from sales_channels.integrations.shopify.models.sales_channels import ShopifySalesChannel
from sales_channels.models.imports import SalesChannelImport


class ShopifyImportUpdateOnlyTests(TransactionTestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._shopify_import_task_patcher = patch(
            "sales_channels.integrations.shopify.tasks.shopify_import_db_task",
            return_value=None,
        )
        self._shopify_import_task_patcher.start()
        self.addCleanup(self._shopify_import_task_patcher.stop)

        self.sales_channel = ShopifySalesChannel.objects.create(
            hostname="https://shopify.example.com",
            access_token="token",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.import_process = SalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            update_only=True,
        )

    @patch("sales_channels.integrations.shopify.factories.imports.imports.ImportProductInstance")
    @patch("sales_channels.integrations.shopify.factories.imports.imports.GetShopifyApiMixin.get_api")
    def test_simple_product_respects_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        mock_get_api.return_value = MagicMock()

        processor = ShopifyImportProcessor(
            self.import_process,
            self.sales_channel,
        )
        processor.get_product_translations = MagicMock(return_value=[])
        processor.get_product_images = MagicMock(return_value=([], {}))
        processor.get_product_prices = MagicMock(return_value=[])
        processor.get_product_attributes = MagicMock(return_value=([], {}, {}))
        processor.get_product_variations = MagicMock(return_value=([], {}))
        processor.update_remote_product = MagicMock()
        processor.create_log_instance = MagicMock()
        processor.handle_ean_code = MagicMock()
        processor.handle_attributes = MagicMock()
        processor.handle_translations = MagicMock()
        processor.handle_prices = MagicMock()
        processor.handle_images = MagicMock()
        processor.handle_variations = MagicMock()
        processor.handle_sales_channels_views = MagicMock()

        instance = MagicMock()
        instance.update_only = False
        mock_import_instance.return_value = instance

        product = {
            "id": "gid://shopify/Product/1",
            "title": "Product",
            "status": "ACTIVE",
            "productType": "Default",
            "variants": {
                "edges": [
                    {"node": {"sku": "SKU1", "inventoryPolicy": "CONTINUE", "barcode": "123"}}
                ]
            },
        }

        processor.get_product_data(product)

        self.assertTrue(instance.update_only)

    @patch("sales_channels.integrations.shopify.factories.imports.imports.ImportProductInstance")
    @patch("sales_channels.integrations.shopify.factories.imports.imports.GetShopifyApiMixin.get_api")
    def test_configurable_product_overrides_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        mock_get_api.return_value = MagicMock()

        processor = ShopifyImportProcessor(
            self.import_process,
            self.sales_channel,
        )
        processor.get_product_translations = MagicMock(return_value=[])
        processor.get_product_images = MagicMock(return_value=([], {}))
        processor.get_product_prices = MagicMock(return_value=[])
        processor.get_product_attributes = MagicMock(return_value=([], {}, {}))
        processor.get_product_variations = MagicMock(return_value=([], {}))
        processor.update_remote_product = MagicMock()
        processor.create_log_instance = MagicMock()
        processor.handle_ean_code = MagicMock()
        processor.handle_attributes = MagicMock()
        processor.handle_translations = MagicMock()
        processor.handle_prices = MagicMock()
        processor.handle_images = MagicMock()
        processor.handle_variations = MagicMock()
        processor.handle_sales_channels_views = MagicMock()

        instance = MagicMock()
        instance.update_only = True
        mock_import_instance.return_value = instance

        product = {
            "id": "gid://shopify/Product/2",
            "title": "Configurable",
            "status": "ACTIVE",
            "productType": "Default",
            "variants": {
                "edges": [
                    {"node": {"sku": "SKU1", "inventoryPolicy": "CONTINUE", "barcode": "123"}},
                    {"node": {"sku": "SKU2", "inventoryPolicy": "CONTINUE", "barcode": "124"}},
                ]
            },
        }

        processor.get_product_data(product)

        self.assertFalse(instance.update_only)
