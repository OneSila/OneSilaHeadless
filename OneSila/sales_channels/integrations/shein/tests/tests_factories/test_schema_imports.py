"""Tests for the Shein schema import processor."""

from unittest.mock import call, patch

from core.tests import TestCase
from products.models import SimpleProduct

from sales_channels.integrations.shein.factories.imports.schema_imports import (
    SheinSchemaImportProcessor,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductCategory,
    SheinSalesChannel,
)
from sales_channels.models import SalesChannelImport


class SheinSchemaImportProcessorTest(TestCase):
    """Ensure the schema import toggles channel state and runs the sync factory."""

    def setUp(self):
        super().setUp()
        self.sales_channel: SheinSalesChannel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://shein.example.com",
            active=True,
            is_importing=False,
            secret_key="secret",
            open_key_id="open",
        )
        self.import_process: SalesChannelImport = SalesChannelImport.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_run_invokes_full_schema_factory(self):
        processor = SheinSchemaImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with patch(
            "sales_channels.integrations.shein.factories.imports.schema_imports.SheinCategoryTreeSyncFactory"
        ) as mock_schema_factory:
            schema_factory_instance = mock_schema_factory.return_value
            schema_factory_instance.synced_document_rules = 3
            schema_factory_instance.synced_document_types_created = 2
            schema_factory_instance.synced_document_types_updated = 1
            processor.run()

        mock_schema_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            language=None,
            import_process=self.import_process,
            sync_document_types=True,
        )
        schema_factory_instance.run.assert_called_once_with()

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, SalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.percentage, 100)

        self.sales_channel.refresh_from_db()
        self.assertTrue(self.sales_channel.active)
        self.assertFalse(self.sales_channel.is_importing)

    def test_run_reinspects_only_products_with_shein_category_on_current_channel(self):
        processor = SheinSchemaImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        current_channel_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        other_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://shein-second.example.com",
            active=True,
            is_importing=False,
            secret_key="secret-2",
            open_key_id="open-2",
        )
        other_channel_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        unrelated_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=self.sales_channel,
            remote_id="cat-current",
            name="Current",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=other_channel,
            remote_id="cat-other",
            name="Other",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=current_channel_product,
            sales_channel=self.sales_channel,
            remote_id="cat-current",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=other_channel_product,
            sales_channel=other_channel,
            remote_id="cat-other",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        with patch(
            "sales_channels.integrations.shein.factories.imports.schema_imports.SheinCategoryTreeSyncFactory"
        ) as mock_schema_factory, patch(
            "products_inspector.models.Inspector.inspect_product",
            autospec=True,
        ) as mock_inspect_product:
            schema_factory_instance = mock_schema_factory.return_value
            schema_factory_instance.synced_document_rules = 0
            schema_factory_instance.synced_document_types_created = 0
            schema_factory_instance.synced_document_types_updated = 0
            processor.run()

        self.assertEqual(mock_inspect_product.mock_calls, [call(current_channel_product.inspector, run_async=False)])
        self.assertNotEqual(other_channel_product.inspector.id, current_channel_product.inspector.id)
        self.assertNotEqual(unrelated_product.inspector.id, current_channel_product.inspector.id)
