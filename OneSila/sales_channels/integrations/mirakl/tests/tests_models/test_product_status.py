from model_bakery import baker

from core.tests import TestCase
from integrations.models import IntegrationLog
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductIssue,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductStatusTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="https://mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
        )
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
            syncing_current_percentage=100,
        )

    def _make_feed_item(self, *, status: str) -> MiraklSalesChannelFeedItem:
        feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
        )
        return baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=feed,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
            status=status,
        )

    def test_latest_pending_feed_item_keeps_product_pending_approval(self):
        self._make_feed_item(status=MiraklSalesChannelFeedItem.STATUS_PENDING)

        self.remote_product.refresh_status(commit=True)
        self.remote_product.refresh_from_db()

        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_PENDING_APPROVAL)

    def test_latest_success_feed_item_marks_product_completed(self):
        self._make_feed_item(status=MiraklSalesChannelFeedItem.STATUS_SUCCESS)

        self.remote_product.refresh_status(commit=True)
        self.remote_product.refresh_from_db()

        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_COMPLETED)

    def test_rejecting_issues_override_successful_feed_item(self):
        self._make_feed_item(status=MiraklSalesChannelFeedItem.STATUS_SUCCESS)
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            code="1000",
            main_code="1000",
            severity="ERROR",
        )

        self.remote_product.refresh_status(commit=True)
        self.remote_product.refresh_from_db()

        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_APPROVAL_REJECTED)

    def test_warning_only_issue_keeps_successful_product_completed(self):
        self._make_feed_item(status=MiraklSalesChannelFeedItem.STATUS_SUCCESS)
        baker.make(
            MiraklProductIssue,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            code="3000",
            main_code="3000",
            severity="WARNING",
        )

        self.remote_product.refresh_status(commit=True)
        self.remote_product.refresh_from_db()

        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_COMPLETED)

    def test_unresolved_sync_errors_still_mark_product_failed(self):
        self._make_feed_item(status=MiraklSalesChannelFeedItem.STATUS_SUCCESS)
        IntegrationLog.objects.create(
            integration=self.sales_channel,
            remote_product=self.remote_product,
            action=IntegrationLog.ACTION_UPDATE,
            status=IntegrationLog.STATUS_FAILED,
        )

        self.remote_product.refresh_status(commit=True)
        self.remote_product.refresh_from_db()

        self.assertEqual(self.remote_product.status, MiraklProduct.STATUS_FAILED)
