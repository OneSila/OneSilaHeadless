from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.mirakl.models import (
    MiraklSalesChannel,
    MiraklSalesChannelImport,
)
from sales_channels.integrations.mirakl.tasks import (
    mirakl_import_db_task,
    sales_channels__tasks__refresh_mirakl_product_issues_differential,
    sales_channels__tasks__refresh_mirakl_product_issues_differential__cronjob,
    sales_channels__tasks__refresh_mirakl_product_issues_full,
    sales_channels__tasks__refresh_mirakl_product_issues_full__cronjob,
)


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

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_differential")
    def test_manual_differential_issue_refresh_task_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_differential(
            sales_channel_id=self.sales_channel.id,
        )

        flow_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_full")
    def test_manual_full_issue_refresh_task_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_full(
            sales_channel_id=self.sales_channel.id,
        )

        flow_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_differential")
    def test_differential_issue_cronjob_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_differential__cronjob()

        flow_mock.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_full")
    def test_full_issue_cronjob_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_full__cronjob()

        flow_mock.assert_called_once_with()

    def test_mirakl_import_db_task_runs_products_processor(self):
        self.import_process.type = MiraklSalesChannelImport.TYPE_PRODUCTS
        self.import_process.save(update_fields=["type"])

        with patch(
            "sales_channels.integrations.mirakl.tasks.MiraklProductsImportProcessor"
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
