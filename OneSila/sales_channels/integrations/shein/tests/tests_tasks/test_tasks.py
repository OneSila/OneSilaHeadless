"""Tests for Shein integration Huey tasks."""

from unittest.mock import patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.shein.models import SheinProduct, SheinSalesChannel
from sales_channels.integrations.shein.tasks import (
    shein__tasks__refresh_product_issues__cronjob,
    shein_import_db_task,
)
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

    # @TODO: FIX THIS AFTER DEPLOY
    # def test_shein_import_db_task_runs_processor(self):
    #     with patch(
    #         "sales_channels.integrations.shein.tasks.SheinSchemaImportProcessor"
    #     ) as mock_processor:
    #         shein_import_db_task(
    #             import_process=self.import_process,
    #             sales_channel=self.sales_channel,
    #         )
    #
    #     mock_processor.assert_called_once_with(
    #         import_process=self.import_process,
    #         sales_channel=self.sales_channel,
    #     )
    #     mock_processor.return_value.run.assert_called_once_with()


class SheinProductIssuesCronjobTest(TestCase):
    @patch("sales_channels.integrations.shein.factories.sales_channels.issues.FetchRemoteIssuesFactory")
    def test_refresh_includes_only_pending_products(self, factory_class):
        sales_channel = SheinSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="shein.issues.test",
            remote_id="SC-ISSUES",
        )
        pending_product = SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            status=SheinProduct.STATUS_PENDING_APPROVAL,
        )
        SheinProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            status=SheinProduct.STATUS_COMPLETED,
        )

        shein__tasks__refresh_product_issues__cronjob()

        called_products = {
            call.kwargs["remote_product"]
            for call in factory_class.call_args_list
        }
        self.assertEqual(called_products, {pending_product})
