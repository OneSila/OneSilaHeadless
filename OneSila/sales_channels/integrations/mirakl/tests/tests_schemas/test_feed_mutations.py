from unittest.mock import patch

from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed


START_MIRAKL_PRODUCT_FEED_MUTATION = """
mutation ($instance: MiraklSalesChannelPartialInput!) {
  startMiraklProductFeed(instance: $instance) {
    id
    status
    type
  }
}
"""


class MiraklFeedMutationTests(TransactionTestCaseMixin, TransactionTestCase):
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

    @patch("sales_channels.integrations.mirakl.flows.sync_mirakl_product_feeds")
    def test_start_product_feed_returns_latest_feed(self, sync_mock):
        feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_PENDING,
        )
        sync_mock.return_value = [feed]

        response = self.strawberry_test_client(
            query=START_MIRAKL_PRODUCT_FEED_MUTATION,
            variables={"instance": {"id": self.to_global_id(self.sales_channel)}},
        )

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["startMiraklProductFeed"]["status"], MiraklSalesChannelFeed.STATUS_PENDING)
        sync_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)
