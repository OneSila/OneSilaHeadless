from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.tests import TransactionTestCase
from products.models import Product
from sales_channels import signals as sc_signals
from sales_channels.integrations.woocommerce.factories.imports.product_imports import (
    WoocommerceProductImportProcessor,
)
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.models.imports import SalesChannelImport


class WoocommerceImportUpdateOnlyTests(TransactionTestCase):
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
            WoocommerceSalesChannel,
            "connect",
            return_value=None,
        )
        self._connect_patcher.start()
        self.addCleanup(self._connect_patcher.stop)

        self.sales_channel = WoocommerceSalesChannel.objects.create(
            hostname="https://woo.example.com",
            api_key="key",
            api_secret="secret",
            api_version=WoocommerceSalesChannel.API_VERSION_3,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.import_process = SalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            update_only=True,
        )

    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.ImportProductInstance")
    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.GetWoocommerceAPIMixin.get_api")
    def test_simple_parent_respects_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        mock_get_api.return_value = MagicMock()

        processor = WoocommerceProductImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.get_structured_product_data = MagicMock(
            return_value=({"type": Product.SIMPLE, "sku": "SKU1"}, False)
        )

        instance = MagicMock()
        instance.update_only = False
        mock_import_instance.return_value = instance

        processor.process_parent_product({"id": "1"})

        self.assertTrue(instance.update_only)

    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.ImportProductInstance")
    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.GetWoocommerceAPIMixin.get_api")
    def test_configurable_parent_overrides_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        mock_get_api.return_value = MagicMock()

        processor = WoocommerceProductImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.get_structured_product_data = MagicMock(
            return_value=({"type": Product.CONFIGURABLE, "sku": "SKU1"}, False)
        )

        instance = MagicMock()
        instance.update_only = True
        mock_import_instance.return_value = instance

        processor.process_parent_product({"id": "1"})

        self.assertFalse(instance.update_only)

    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.ImportProductInstance")
    @patch("sales_channels.integrations.woocommerce.factories.imports.product_imports.GetWoocommerceAPIMixin.get_api")
    def test_variation_respects_update_only(self, mock_get_api, mock_import_instance, *, _unused=None):
        mock_get_api.return_value = MagicMock()

        processor = WoocommerceProductImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor.get_base_product_data = MagicMock(
            return_value=({"type": Product.SIMPLE, "sku": "VSKU"}, True, False)
        )
        processor.get_properties_data_for_product = MagicMock(return_value=[])
        processor.get_images = MagicMock(return_value=[])
        processor.get_prices = MagicMock(return_value=[])
        processor.get_tax_class = MagicMock(return_value=None)

        instance = MagicMock()
        instance.update_only = False
        mock_import_instance.return_value = instance

        parent_instance = SimpleNamespace(
            remote_instance=SimpleNamespace(remote_id="parent"),
            instance=SimpleNamespace(sku="PARENT"),
        )

        processor.process_variation("var1", parent_instance, parent_data={})

        self.assertTrue(instance.update_only)
