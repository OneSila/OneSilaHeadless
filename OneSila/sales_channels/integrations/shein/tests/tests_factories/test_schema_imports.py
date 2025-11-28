"""Tests for the Shein schema import processor."""

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.factories.imports.schema_imports import (
    SheinSchemaImportProcessor,
)
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.models import SalesChannelImport


class SheinSchemaImportProcessorTest(TestCase):
    """Ensure the schema import toggles channel state and runs the sync factory."""

    def setUp(self):
        super().setUp()
        self.sales_channel: SheinSalesChannel = baker.make(
            SheinSalesChannel,
            hostname="https://shein.example.com",
            active=True,
            is_importing=False,
            secret_key="secret",
            open_key_id="open",
        )
        self.import_process: SalesChannelImport = baker.make(
            SalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

    def test_run_invokes_full_schema_factory(self):
        processor = SheinSchemaImportProcessor(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )

        with patch(
            "sales_channels.integrations.shein.factories.imports.schema_imports.SheinCategoryTreeSyncFactory"
        ) as mock_factory:
            factory_instance = mock_factory.return_value
            processor.run()

        mock_factory.assert_called_once_with(
            sales_channel=self.sales_channel,
            view=None,
            language=None,
            import_process=self.import_process,
        )
        factory_instance.run.assert_called_once_with()

        self.import_process.refresh_from_db()
        self.assertEqual(self.import_process.status, SalesChannelImport.STATUS_SUCCESS)
        self.assertEqual(self.import_process.percentage, 100)

        self.sales_channel.refresh_from_db()
        self.assertTrue(self.sales_channel.active)
        self.assertFalse(self.sales_channel.is_importing)
