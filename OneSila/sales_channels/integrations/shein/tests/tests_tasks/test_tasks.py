"""Tests for Shein integration Huey tasks."""

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.tasks import shein_import_db_task
from sales_channels.models import SalesChannelImport


class SheinImportTasksTest(TestCase):
    """Validate the orchestration performed by the Shein Huey tasks."""

    def setUp(self):
        super().setUp()
        self.sales_channel: SheinSalesChannel = baker.make(
            SheinSalesChannel,
            hostname="https://tasks.shein.example.com",
            secret_key="secret",
            open_key_id="open",
        )
        self.import_process = baker.make(
            SalesChannelImport,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

    def test_shein_import_db_task_runs_processor(self):
        with patch(
            "sales_channels.integrations.shein.tasks.SheinSchemaImportProcessor"
        ) as mock_processor:
            shein_import_db_task(
                import_process=self.import_process,
                sales_channel=self.sales_channel,
            )

        mock_processor.assert_called_once_with(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        mock_processor.return_value.run.assert_called_once_with()
