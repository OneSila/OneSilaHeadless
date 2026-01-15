from unittest.mock import MagicMock, patch

from core.tests import TransactionTestCase
from django.utils import timezone
from products.product_types import CONFIGURABLE, SIMPLE
from sales_channels import signals as sc_signals
from sales_channels.integrations.ebay.factories.imports.products_imports import (
    EbayProductsImportProcessor,
)
from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.models.imports import SalesChannelImport


class EbayImportUpdateOnlyTests(TransactionTestCase):
    def setUp(self, *, _unused=None):
        super().setUp()
        self._sales_channel_created_patcher = patch.object(
            sc_signals.sales_channel_created,
            "send",
            return_value=[],
        )
        self._sales_channel_created_patcher.start()
        self.addCleanup(self._sales_channel_created_patcher.stop)

        self._ebay_import_task_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_import_db_task",
            return_value=None,
        )
        self._ebay_import_task_patcher.start()
        self.addCleanup(self._ebay_import_task_patcher.stop)

        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay.example.com",
            environment=EbaySalesChannel.PRODUCTION,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            refresh_token_expiration=timezone.now() + timezone.timedelta(days=1),
        )
        self.import_process = SalesChannelImport.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            update_only=True,
        )

    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.ImportProductInstance")
    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.GetEbayAPIMixin.get_api")
    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.get_is_product_variation")
    def test_simple_product_respects_update_only(
        self,
        mock_get_is_variation,
        mock_get_api,
        mock_import_instance,
        *,
        _unused=None,
    ):
        mock_get_is_variation.return_value = (False, None)
        mock_get_api.return_value = MagicMock()

        processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor._extract_sku = MagicMock(return_value="SKU1")
        processor.get_product_rule = MagicMock(return_value=None)
        processor.get__product_data = MagicMock(return_value=({"type": SIMPLE, "sku": "SKU1"}, None, None))
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

        processor.process_product_item(
            product_data={},
            offer_data={"marketplaceId": "EBAY_GB"},
        )

        self.assertTrue(instance.update_only)

    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.ImportProductInstance")
    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.GetEbayAPIMixin.get_api")
    @patch("sales_channels.integrations.ebay.factories.imports.products_imports.get_is_product_variation")
    def test_configurable_product_overrides_update_only(
        self,
        mock_get_is_variation,
        mock_get_api,
        mock_import_instance,
        *,
        _unused=None,
    ):
        mock_get_is_variation.return_value = (False, None)
        mock_get_api.return_value = MagicMock()

        processor = EbayProductsImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        processor._extract_sku = MagicMock(return_value="SKU1")
        processor.get_product_rule = MagicMock(return_value=None)
        processor.get__product_data = MagicMock(return_value=({"type": CONFIGURABLE, "sku": "SKU1"}, None, None))
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

        processor.process_product_item(
            product_data={},
            offer_data={"marketplaceId": "EBAY_GB"},
        )

        self.assertFalse(instance.update_only)
