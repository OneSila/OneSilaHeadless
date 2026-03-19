from unittest.mock import Mock, patch

from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)
from sales_channels.integrations.mirakl.flows import (
    refresh_mirakl_product_issues_full,
    sync_mirakl_product_import_statuses,
)
from sales_channels.integrations.mirakl.tasks import (
    _queue_delete_rows_for_mirakl_remote_products,
    mirakl_import_db_task,
    sales_channels__tasks__sync_mirakl_product_import_statuses,
    sales_channels__tasks__sync_mirakl_product_import_statuses__cronjob,
    sales_channels__tasks__refresh_mirakl_product_issues_differential,
    sales_channels__tasks__refresh_mirakl_product_issues_differential__cronjob,
    sales_channels__tasks__refresh_mirakl_product_issues_full,
    sales_channels__tasks__refresh_mirakl_product_issues_full__cronjob,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklImportTaskTests(DisableMiraklConnectionMixin, TestCase):
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

    @patch("sales_channels.integrations.mirakl.flows.sync_mirakl_product_import_statuses")
    def test_manual_product_import_status_sync_task_calls_flow(self, flow_mock):
        sales_channels__tasks__sync_mirakl_product_import_statuses(
            sales_channel_id=self.sales_channel.id,
        )

        flow_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)

    @patch("sales_channels.integrations.mirakl.flows.sync_mirakl_product_import_statuses")
    def test_product_import_status_sync_cronjob_calls_flow(self, flow_mock):
        sales_channels__tasks__sync_mirakl_product_import_statuses__cronjob()

        flow_mock.assert_called_once_with()

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

    @patch("sales_channels.integrations.mirakl.tasks.MiraklProductDeleteFactory")
    def test_delete_helper_falls_back_to_all_views_when_assign_is_missing(self, delete_factory_mock):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
        )

        processed_ids = _queue_delete_rows_for_mirakl_remote_products(
            sales_channel_id=self.sales_channel.id,
            remote_product_ids=[remote_product.id],
        )

        self.assertEqual(processed_ids, [remote_product.id])
        delete_factory_mock.assert_called_once_with(
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_instance=remote_product,
            view=view,
        )
        delete_factory_mock.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.flows.feeds.MiraklImportStatusSyncFactory")
    def test_import_status_flow_skips_active_but_disconnected_channels(self, sync_factory_mock):
        disconnected_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://mirakl.example.com",
            shop_id=None,
            api_key="",
        )

        result = sync_mirakl_product_import_statuses(sales_channel_id=disconnected_channel.id)

        self.assertEqual(result, [])
        sync_factory_mock.assert_not_called()

    @patch("sales_channels.integrations.mirakl.flows.feeds.MiraklImportStatusSyncFactory")
    def test_import_status_flow_continues_when_one_channel_fails(self, sync_factory_mock):
        good_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://good.example.com",
            shop_id=1,
            api_key="token-1",
        )
        bad_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://bad.example.com",
            shop_id=2,
            api_key="token-2",
        )

        def build_factory(*, sales_channel):
            fac = Mock()
            if sales_channel.id == bad_channel.id:
                fac.run.side_effect = ValueError("boom")
            else:
                fac.run.return_value = [{"sales_channel_id": sales_channel.id}]
            return fac

        sync_factory_mock.side_effect = build_factory

        result = sync_mirakl_product_import_statuses()

        self.assertEqual(result, [{"sales_channel_id": good_channel.id}])

    @patch("sales_channels.integrations.mirakl.flows.issues.MiraklProductIssuesFetchFactory")
    def test_full_issues_flow_continues_when_one_channel_fails(self, issues_factory_mock):
        good_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://good-issues.example.com",
            shop_id=11,
            api_key="token-11",
        )
        bad_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://bad-issues.example.com",
            shop_id=22,
            api_key="token-22",
        )

        def build_factory(*, sales_channel, mode):
            fac = Mock()
            self.assertEqual(mode, "full")
            if sales_channel.id == bad_channel.id:
                fac.run.side_effect = ValueError("boom")
            else:
                fac.run.return_value = {"sales_channel_id": sales_channel.id}
            return fac

        issues_factory_mock.side_effect = build_factory

        result = refresh_mirakl_product_issues_full()

        self.assertEqual(result, [{"sales_channel_id": good_channel.id}])
