from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from core.tests import TestCase
from django.utils import timezone
from integrations.helpers import get_import_path
from integrations.models import IntegrationTaskQueue
from model_bakery import baker

from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelFeed,
    MiraklSalesChannelView,
)
from sales_channels.integrations.mirakl.flows import (
    refresh_mirakl_product_issues_differential,
    refresh_mirakl_product_issues_full,
)
from sales_channels.integrations.mirakl.tasks import (
    _queue_delete_rows_for_mirakl_remote_products,
    mirakl_import_db_task,
    process_mirakl_feed_db_task,
    sales_channels__tasks__sync_mirakl_product_feeds,
    sales_channels__tasks__sync_mirakl_product_feeds__cronjob,
    sync_mirakl_product_import_statuses_db_task,
    sales_channels__tasks__sync_mirakl_product_import_statuses,
    sales_channels__tasks__sync_mirakl_product_import_statuses__cronjob,
    sales_channels__tasks__refresh_mirakl_product_issues_differential,
    sales_channels__tasks__refresh_mirakl_product_issues_differential__cronjob,
    sales_channels__tasks__refresh_mirakl_product_issues_full,
    sales_channels__tasks__refresh_mirakl_product_issues_full__cronjob,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


def _noop_dispatch_task(self, *, _unused=None):
    return None


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

    @patch(
        "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
        new=_noop_dispatch_task,
    )
    def test_sync_mirakl_product_feeds_task_marks_gathering_feeds_ready_and_queues_remote_task(self, *, _unused=None):
        gathering_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        )
        baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
        )

        processed_feeds = sales_channels__tasks__sync_mirakl_product_feeds.call_local(
            sales_channel_id=self.sales_channel.id,
        )

        gathering_feed.refresh_from_db()
        self.assertEqual(len(processed_feeds), 1)
        self.assertEqual(processed_feeds[0].id, gathering_feed.id)
        self.assertEqual(gathering_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)

    @patch(
        "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
        new=_noop_dispatch_task,
    )
    def test_sync_mirakl_product_feeds_cronjob_marks_gathering_feeds_ready_and_queues_remote_task(self, *, _unused=None):
        gathering_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        )

        processed_feeds = sales_channels__tasks__sync_mirakl_product_feeds__cronjob.call_local()

        gathering_feed.refresh_from_db()
        self.assertEqual([feed.id for feed in processed_feeds], [gathering_feed.id])
        self.assertEqual(gathering_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)

    @patch(
        "sales_channels.integrations.mirakl.tasks.BaseRemoteTask",
    )
    @patch(
        "sales_channels.integrations.mirakl.factories.feeds.MiraklProductFeedBuildFactory",
    )
    def test_process_mirakl_feed_remote_task_runs_single_feed_factory(
        self,
        build_factory_mock,
        base_remote_task_mock,
    ):
        feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
        )
        task_instance = base_remote_task_mock.return_value

        def execute_side_effect(callable_obj):
            callable_obj()

        task_instance.execute.side_effect = execute_side_effect

        process_mirakl_feed_db_task.call_local(
            1,
            feed_id=feed.id,
        )

        base_remote_task_mock.assert_called_once_with(1)
        build_factory_mock.assert_called_once()
        self.assertEqual(build_factory_mock.call_args.kwargs["feed"].id, feed.id)
        build_factory_mock.return_value.run.assert_called_once_with()

    @patch(
        "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
        new=_noop_dispatch_task,
    )
    def test_manual_product_import_status_sync_task_queues_remote_task(self, *, _unused=None):
        queued_sales_channel_ids = sales_channels__tasks__sync_mirakl_product_import_statuses.call_local(
            sales_channel_id=self.sales_channel.id,
        )

        self.assertEqual(queued_sales_channel_ids, [self.sales_channel.id])
        tasks = IntegrationTaskQueue.objects.filter(task_name=get_import_path(sync_mirakl_product_import_statuses_db_task))
        self.assertEqual(tasks.count(), 1)
        task = tasks.get()
        self.assertEqual(task.integration_id, self.sales_channel.id)
        self.assertEqual(task.task_kwargs, {"sales_channel_id": self.sales_channel.id})

    @patch(
        "integrations.factories.task_queue.TaskQueueFactory.dispatch_task",
        new=_noop_dispatch_task,
    )
    def test_product_import_status_sync_cronjob_queues_remote_task(self, *, _unused=None):
        disconnected_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://disconnected.example.com",
            shop_id=None,
            api_key="",
        )
        not_due_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://fresh.example.com",
            shop_id=456,
            api_key="fresh-token",
            last_product_imports_request_date=timezone.now(),
        )

        queued_sales_channel_ids = sales_channels__tasks__sync_mirakl_product_import_statuses__cronjob.call_local()

        self.assertEqual(queued_sales_channel_ids, [self.sales_channel.id])
        tasks = IntegrationTaskQueue.objects.filter(task_name=get_import_path(sync_mirakl_product_import_statuses_db_task))
        self.assertEqual(tasks.count(), 1)
        task = tasks.get()
        self.assertEqual(task.integration_id, self.sales_channel.id)
        self.assertEqual(task.task_kwargs, {"sales_channel_id": self.sales_channel.id})
        self.assertEqual(task.number_of_remote_requests, 1)
        self.assertNotEqual(task.integration_id, disconnected_channel.id)
        self.assertNotEqual(task.integration_id, not_due_channel.id)

    @patch("sales_channels.integrations.mirakl.tasks.BaseRemoteTask")
    @patch("sales_channels.integrations.mirakl.factories.feeds.MiraklImportStatusSyncFactory")
    def test_product_import_status_sync_remote_task_runs_factory(
        self,
        sync_factory_mock,
        base_remote_task_mock,
    ):
        task_instance = base_remote_task_mock.return_value

        def execute_side_effect(callable_obj):
            callable_obj()

        task_instance.execute.side_effect = execute_side_effect

        sync_mirakl_product_import_statuses_db_task.call_local(
            1,
            sales_channel_id=self.sales_channel.id,
        )

        base_remote_task_mock.assert_called_once_with(1)
        sync_factory_mock.assert_called_once_with(sales_channel=self.sales_channel)
        sync_factory_mock.return_value.run.assert_called_once_with()

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_differential")
    def test_manual_differential_issue_refresh_task_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_differential.call_local(
            sales_channel_id=self.sales_channel.id,
        )

        flow_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)

    @patch("sales_channels.integrations.mirakl.flows.refresh_mirakl_product_issues_full")
    def test_manual_full_issue_refresh_task_calls_flow(self, flow_mock):
        sales_channels__tasks__refresh_mirakl_product_issues_full.call_local(
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

    @patch("sales_channels.integrations.mirakl.factories.feeds.MiraklProductDeleteFactory")
    def test_delete_helper_falls_back_to_all_views_when_assign_is_missing(self, delete_factory_mock):
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
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

    @patch("sales_channels.integrations.mirakl.flows.issues.MiraklProductIssuesFetchFactory")
    def test_full_issues_flow_continues_when_one_channel_fails(self, issues_factory_mock):
        self.sales_channel.last_full_issues_fetch = timezone.now()
        self.sales_channel.save(update_fields=["last_full_issues_fetch"])
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
        issues_factory_mock.MODE_FULL = "full"

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

    @patch("sales_channels.integrations.mirakl.flows.issues.timezone.now")
    @patch("sales_channels.integrations.mirakl.flows.issues.MiraklProductIssuesFetchFactory")
    def test_differential_issues_flow_only_processes_channels_due_after_six_hours(self, issues_factory_mock, now_mock):
        now = timezone.make_aware(datetime(2026, 3, 23, 12, 0, 0))
        now_mock.return_value = now
        stale_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://stale-diff.example.com",
            shop_id=33,
            api_key="token-33",
            last_full_issues_fetch=now,
            last_differential_issues_fetch=now - timedelta(hours=6, minutes=1),
        )
        baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://fresh-diff.example.com",
            shop_id=44,
            api_key="token-44",
            last_full_issues_fetch=now,
            last_differential_issues_fetch=now - timedelta(hours=5, minutes=59),
        )
        issues_factory_mock.MODE_DIFFERENTIAL = "differential"
        issues_factory_mock.return_value.run.return_value = {"sales_channel_id": stale_channel.id}

        result = refresh_mirakl_product_issues_differential()

        self.assertEqual(result, [{"sales_channel_id": stale_channel.id}])
        issues_factory_mock.assert_called_once_with(
            sales_channel=stale_channel,
            mode="differential",
        )

    @patch("sales_channels.integrations.mirakl.flows.issues.timezone.now")
    @patch("sales_channels.integrations.mirakl.flows.issues.MiraklProductIssuesFetchFactory")
    def test_full_issues_flow_only_processes_channels_due_after_twenty_four_hours(self, issues_factory_mock, now_mock):
        now = timezone.make_aware(datetime(2026, 3, 23, 12, 0, 0))
        now_mock.return_value = now
        self.sales_channel.last_full_issues_fetch = now
        self.sales_channel.save(update_fields=["last_full_issues_fetch"])
        stale_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://stale-full.example.com",
            shop_id=55,
            api_key="token-55",
            last_full_issues_fetch=now - timedelta(hours=24, minutes=1),
        )
        baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://fresh-full.example.com",
            shop_id=66,
            api_key="token-66",
            last_full_issues_fetch=now - timedelta(hours=23, minutes=59),
        )
        issues_factory_mock.MODE_FULL = "full"
        issues_factory_mock.return_value.run.return_value = {"sales_channel_id": stale_channel.id}

        result = refresh_mirakl_product_issues_full()

        self.assertEqual(result, [{"sales_channel_id": stale_channel.id}])
        issues_factory_mock.assert_called_once_with(
            sales_channel=stale_channel,
            mode="full",
        )
