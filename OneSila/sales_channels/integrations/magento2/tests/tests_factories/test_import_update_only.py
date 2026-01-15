from unittest.mock import MagicMock, patch

from core.tests import TransactionTestCase
from products.models import Product
from sales_channels import signals as sc_signals
from sales_channels.integrations.magento2.factories.imports.imports import MagentoImportProcessor
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.models.imports import SalesChannelImport


class MagentoImportUpdateOnlyTests(TransactionTestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._connect_patcher = patch.object(
            MagentoSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.import_process = SalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            update_only=True,
        )

    @patch("sales_channels.integrations.magento2.factories.imports.imports.ImportProductInstance")
    @patch("sales_channels.integrations.magento2.factories.imports.imports.GetMagentoAPIMixin.get_api")
    def test_simple_product_respects_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        api = MagicMock()
        mock_get_api.return_value = api
        products_api = api.products
        products_api.add_criteria.return_value.execute_search.return_value = [MagicMock()]
        products_api.next.side_effect = ValueError

        processor = MagentoImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.get_product_rule = MagicMock(return_value=None)
        processor.get_product_data = MagicMock(return_value={"type": Product.SIMPLE, "sku": "SKU1"})
        processor.is_magento_variation = MagicMock(return_value=False)
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

        processor.import_products_process()

        self.assertTrue(instance.update_only)

    @patch("sales_channels.integrations.magento2.factories.imports.imports.ImportProductInstance")
    @patch("sales_channels.integrations.magento2.factories.imports.imports.GetMagentoAPIMixin.get_api")
    def test_configurable_product_overrides_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        api = MagicMock()
        mock_get_api.return_value = api
        products_api = api.products
        products_api.add_criteria.return_value.execute_search.return_value = [MagicMock()]
        products_api.next.side_effect = ValueError

        processor = MagentoImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.get_product_rule = MagicMock(return_value=None)
        processor.get_product_data = MagicMock(return_value={"type": Product.CONFIGURABLE, "sku": "SKU1"})
        processor.is_magento_variation = MagicMock(return_value=False)
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

        processor.import_products_process()

        self.assertFalse(instance.update_only)
