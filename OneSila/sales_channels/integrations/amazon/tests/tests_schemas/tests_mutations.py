from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import Product
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


BULK_RESYNC_AMAZON_PRODUCT_MUTATION = """
mutation ($assigns: [SalesChannelViewAssignPartialInput!]!, $forceFullUpdate: Boolean!) {
  bulkResyncAmazonProductFromAssigns(assigns: $assigns, forceFullUpdate: $forceFullUpdate)
}
"""

BULK_REFRESH_AMAZON_LATEST_ISSUES_MUTATION = """
mutation ($assigns: [SalesChannelViewAssignPartialInput!]!) {
  bulkRefreshAmazonLatestIssuesFromAssigns(assigns: $assigns)
}
"""


class AmazonProductMutationTest(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            is_default=True,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = baker.make(
            AmazonProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="ASIN-1",
            remote_sku="SKU-1",
            syncing_current_percentage=100,
        )

    @patch("sales_channels.integrations.amazon.receivers.run_single_amazon_product_task_flow")
    @patch("sales_channels.signals.manual_sync_remote_product.send")
    def test_bulk_resync_amazon_product_from_assigns_sends_signal(self, send_mock, _run_flow):
        assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

        resp = self.strawberry_test_client(
            query=BULK_RESYNC_AMAZON_PRODUCT_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(assign)}],
                "forceFullUpdate": True,
            },
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data["bulkResyncAmazonProductFromAssigns"])
        send_mock.assert_called_once()
        _, kwargs = send_mock.call_args
        self.assertEqual(kwargs["instance"].id, self.remote_product.id)
        self.assertEqual(kwargs["view"].id, self.view.id)
        self.assertFalse(kwargs["force_validation_only"])
        self.assertTrue(kwargs["force_full_update"])

    @patch("sales_channels.integrations.amazon.receivers.run_single_amazon_product_task_flow")
    @patch("sales_channels.integrations.amazon.factories.sales_channels.issues.FetchRemoteIssuesFactory")
    def test_bulk_refresh_amazon_latest_issues_from_assigns_runs_factory(self, factory_mock, _run_flow):
        assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

        resp = self.strawberry_test_client(
            query=BULK_REFRESH_AMAZON_LATEST_ISSUES_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(assign)}],
            },
        )

        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data["bulkRefreshAmazonLatestIssuesFromAssigns"])
        factory_mock.assert_called_once()
        _, kwargs = factory_mock.call_args
        self.assertEqual(kwargs["remote_product"].id, self.remote_product.id)
        self.assertEqual(kwargs["view"].id, self.view.id)
        factory_mock.return_value.run.assert_called_once()
