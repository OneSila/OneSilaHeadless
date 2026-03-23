from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedBuildFactory
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductType,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductFeedBuildFactoryTests(DisableMiraklConnectionMixin, TestCase):
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
        self.product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
        )

    def _make_ready_feed(self):
        return baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
            product_type=self.product_type,
            sales_channel_view=self.view,
        )

    def _add_feed_item(self, *, feed):
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
        return baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=feed,
            remote_product=remote_product,
            sales_channel_view=self.view,
            payload_data=[{"sku": "SKU-1"}],
        )

    def test_run_returns_none_and_resets_feed_to_gathering_when_group_has_active_feed(self):
        ready_feed = self._make_ready_feed()
        baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_SUBMITTED,
            product_type=self.product_type,
            sales_channel_view=self.view,
        )

        result = MiraklProductFeedBuildFactory(feed=ready_feed).run()

        ready_feed.refresh_from_db()
        self.assertIsNone(result)
        self.assertEqual(ready_feed.status, MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS)

    def test_run_deletes_feed_without_rows(self):
        ready_feed = self._make_ready_feed()

        result = MiraklProductFeedBuildFactory(feed=ready_feed).run()

        self.assertIsNone(result)
        self.assertFalse(MiraklSalesChannelFeed.objects.filter(id=ready_feed.id).exists())

    @patch("sales_channels.integrations.mirakl.factories.feeds.build.MiraklProductFeedFileFactory.run")
    def test_run_resets_feed_to_ready_when_rendering_fails(self, render_mock):
        ready_feed = self._make_ready_feed()
        self._add_feed_item(feed=ready_feed)
        render_mock.side_effect = ValueError("boom")

        with self.assertRaises(ValueError):
            MiraklProductFeedBuildFactory(feed=ready_feed).run()

        ready_feed.refresh_from_db()
        self.assertEqual(ready_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)

    @patch("sales_channels.integrations.mirakl.factories.feeds.build.MiraklProductFeedFileFactory.run")
    def test_run_resets_feed_to_ready_when_sales_channel_is_disconnected(self, render_mock):
        ready_feed = self._make_ready_feed()
        self._add_feed_item(feed=ready_feed)
        self.sales_channel.hostname = ""
        self.sales_channel.save(update_fields=["hostname"])

        result = MiraklProductFeedBuildFactory(feed=ready_feed).run()

        ready_feed.refresh_from_db()
        self.assertEqual(result.id, ready_feed.id)
        self.assertEqual(ready_feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)
        render_mock.assert_called_once_with()
