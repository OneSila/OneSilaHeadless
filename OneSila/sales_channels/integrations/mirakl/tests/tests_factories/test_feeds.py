from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from core.tests import TestCase
from model_bakery import baker

from products.models import Product
from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklProductFeedBuildFactory,
    mark_remote_products_for_mirakl_feed_updates,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelFeedItem, SalesChannelViewAssign


class MiraklFeedFactoryTests(TestCase):
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
            remote_id="WEB",
            name="Web",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            sku="MIR-001",
            name="Mirakl Product",
            type="SIMPLE",
            active=True,
        )
        baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            product=self.product,
        )

    def test_marking_creates_remote_product_and_gathering_feed_item(self):
        mark_remote_products_for_mirakl_feed_updates(product_ids=[self.product.id])

        remote_product = MiraklProduct.objects.get(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        feed = MiraklSalesChannelFeed.objects.get(
            sales_channel=self.sales_channel,
            status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        )
        item = SalesChannelFeedItem.objects.get(feed=feed, remote_product=remote_product)

        self.assertEqual(item.action, SalesChannelFeedItem.ACTION_CREATE)
        self.assertTrue(item.payload_data["rows"])
        assign = SalesChannelViewAssign.objects.get(product=self.product, sales_channel_view=self.view)
        self.assertEqual(assign.remote_product_id, remote_product.id)

    @patch("sales_channels.integrations.mirakl.factories.feeds.build.MiraklProductFeedSubmitFactory")
    def test_build_factory_creates_feed_file_and_items(self, submit_factory_cls):
        mark_remote_products_for_mirakl_feed_updates(product_ids=[self.product.id])
        feed = MiraklSalesChannelFeed.objects.get(sales_channel=self.sales_channel)
        MiraklSalesChannelFeed.objects.filter(id=feed.id).update(updated_at=timezone.now() - timedelta(minutes=21))

        feed = MiraklProductFeedBuildFactory(sales_channel=self.sales_channel).run()

        self.assertIsInstance(feed, MiraklSalesChannelFeed)
        self.assertTrue(feed.file)
        self.assertEqual(feed.type, MiraklSalesChannelFeed.TYPE_PRODUCT)
        self.assertEqual(feed.stage, MiraklSalesChannelFeed.STAGE_PRODUCT)
        self.assertEqual(feed.status, MiraklSalesChannelFeed.STATUS_READY_TO_RENDER)
        item = SalesChannelFeedItem.objects.get(feed=feed)
        self.assertEqual(item.action, SalesChannelFeedItem.ACTION_CREATE)
        self.assertTrue(item.payload_data["rows"])
        submit_factory_cls.assert_called_once_with(feed=feed)
        submit_factory_cls.return_value.run.assert_called_once_with()
