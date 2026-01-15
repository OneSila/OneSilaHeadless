from unittest.mock import MagicMock, patch

from core.tests import TransactionTestCase
from products.product_types import CONFIGURABLE, SIMPLE
from sales_channels import signals as sc_signals
from sales_channels.integrations.shein.factories.imports.products import (
    SheinProductsImportProcessor,
)
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.models.imports import SheinSalesChannelImport


class SheinImportUpdateOnlyTests(TransactionTestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._shein_import_task_patcher = patch(
            "sales_channels.integrations.shein.tasks.shein_import_db_task",
            return_value=None,
        )
        self._shein_import_task_patcher.start()
        self.addCleanup(self._shein_import_task_patcher.stop)

        self.sales_channel = SheinSalesChannel.objects.create(
            hostname="shein",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.import_process = SheinSalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=SheinSalesChannelImport.TYPE_PRODUCTS,
            update_only=True,
        )

    @patch("sales_channels.integrations.shein.factories.imports.products.ImportProductInstance")
    def test_simple_product_respects_update_only(self, mock_import_instance, *, _unused=None):
        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor._resolve_local_sku = MagicMock(return_value="SKU1")
        processor._get_remote_product = MagicMock(return_value=None)
        processor.get__product_data = MagicMock(return_value=({"type": SIMPLE, "sku": "SKU1"}, None, None))
        processor.update_remote_product = MagicMock()
        processor.handle_translations = MagicMock()
        processor.handle_images = MagicMock()
        processor.handle_ean_code = MagicMock()
        processor.handle_attributes = MagicMock()
        processor.handle_prices = MagicMock()
        processor.handle_variations = MagicMock()
        processor.handle_sales_channels_views = MagicMock()

        instance = MagicMock()
        instance.update_only = False
        mock_import_instance.return_value = instance

        processor._process_single_product_entry(
            spu_payload={},
            skc_payload={},
            sku_payload={},
            rule=None,
            is_variation=False,
            is_configurable=False,
            parent_sku=None,
        )

        self.assertTrue(instance.update_only)

    @patch("sales_channels.integrations.shein.factories.imports.products.ImportProductInstance")
    def test_configurable_product_overrides_update_only(self, mock_import_instance, *, _unused=None):
        processor = SheinProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor._resolve_local_sku = MagicMock(return_value="SKU1")
        processor._get_remote_product = MagicMock(return_value=None)
        processor.get__product_data = MagicMock(return_value=({"type": CONFIGURABLE, "sku": "SKU1"}, None, None))
        processor.update_remote_product = MagicMock()
        processor.handle_translations = MagicMock()
        processor.handle_images = MagicMock()
        processor.handle_ean_code = MagicMock()
        processor.handle_attributes = MagicMock()
        processor.handle_prices = MagicMock()
        processor.handle_variations = MagicMock()
        processor.handle_sales_channels_views = MagicMock()

        instance = MagicMock()
        instance.update_only = True
        mock_import_instance.return_value = instance

        processor._process_single_product_entry(
            spu_payload={},
            skc_payload={},
            sku_payload={},
            rule=None,
            is_variation=False,
            is_configurable=True,
            parent_sku=None,
        )

        self.assertFalse(instance.update_only)
