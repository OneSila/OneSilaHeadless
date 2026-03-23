from unittest.mock import patch

from django.core.exceptions import ValidationError
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklFeedResyncFactory
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductType,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklFeedResyncFactoryTests(DisableMiraklConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
        )
        self.product_type = baker.make(
            MiraklProductType,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_run_requires_concluded_feed(self):
        feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
            product_type=self.product_type,
        )

        with self.assertRaises(ValidationError):
            MiraklFeedResyncFactory(feed=feed).run()

    @patch("sales_channels.integrations.mirakl.factories.feeds.resync.MiraklProductPayloadBuilder.build")
    def test_run_creates_new_feed_and_regenerates_payloads(
        self,
        build_mock,
    ):
        source_feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_PARTIAL,
            remote_id="2008",
            product_remote_id="2008",
            import_status="COMPLETE",
            product_type=self.product_type,
        )
        remote_product = baker.make(
            MiraklProduct,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            MiraklSalesChannelFeedItem,
            feed=source_feed,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=remote_product,
            identifier="SKU-1",
            payload_data=[{"old": "payload"}],
        )
        build_mock.return_value = (self.product_type, [{"sku": "SKU-1", "title": "Fresh"}])

        resynced_feed = MiraklFeedResyncFactory(feed=source_feed).run()

        source_feed.refresh_from_db()
        new_item = MiraklSalesChannelFeedItem.objects.get(feed=resynced_feed)

        self.assertNotEqual(resynced_feed.id, source_feed.id)
        self.assertEqual(resynced_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)
        self.assertEqual(resynced_feed.remote_id, "")
        self.assertEqual(resynced_feed.items_count, 1)
        self.assertEqual(resynced_feed.rows_count, 1)
        self.assertEqual(new_item.payload_data, [{"sku": "SKU-1", "title": "Fresh"}])
        self.assertEqual(source_feed.items.first().payload_data, [{"old": "payload"}])
