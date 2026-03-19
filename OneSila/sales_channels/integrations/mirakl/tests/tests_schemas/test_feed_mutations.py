from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


RESYNC_MIRAKL_FEED_MUTATION = """
mutation ($instance: SalesChannelFeedPartialInput!) {
  resyncMiraklFeed(instance: $instance) {
    id
    status
    type
  }
}
"""

REMOVED_START_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  startMiraklProductFeed(instance: $instance) {
    id
  }
}
"""


class MiraklFeedMutationTests(
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret-token",
        )

    @patch("sales_channels.integrations.mirakl.flows.resync_mirakl_feed")
    def test_resync_feed_returns_new_feed(self, flow_mock):
        source_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUCCESS,
        )
        resynced_feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
        )
        flow_mock.return_value = resynced_feed

        response = self.strawberry_test_client(
            query=RESYNC_MIRAKL_FEED_MUTATION,
            variables={"instance": {"id": self.to_global_id(source_feed)}},
        )

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["resyncMiraklFeed"]["status"], MiraklSalesChannelFeed.STATUS_SUBMITTED)
        flow_mock.assert_called_once_with(feed_id=source_feed.id)

    def test_removed_start_mutation_is_absent(self):
        response = self.strawberry_test_client(
            query=REMOVED_START_MUTATION,
            variables={"instance": {"id": self.to_global_id(self.sales_channel)}},
        )

        self.assertIsNotNone(response.errors)
        self.assertIn("startMiraklProductFeed", str(response.errors[0]))
