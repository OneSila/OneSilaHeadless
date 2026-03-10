from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.mirakl.models import (
    MiraklSalesChannel,
    MiraklSalesChannelImport,
)
from sales_channels.integrations.mirakl.tasks import mirakl_import_db_task


class MiraklImportTaskTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.import_process = baker.make(
            MiraklSalesChannelImport,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelImport.TYPE_SCHEMA,
        )

    def test_mirakl_import_db_task_runs_schema_processor(self):
        with patch(
            "sales_channels.integrations.mirakl.tasks.MiraklSchemaImportProcessor"
        ) as mock_processor:
            mirakl_import_db_task(
                import_process=self.import_process,
                sales_channel=self.sales_channel,
            )

        mock_processor.assert_called_once_with(
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        mock_processor.return_value.run.assert_called_once_with()
