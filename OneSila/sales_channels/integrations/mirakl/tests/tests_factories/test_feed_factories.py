from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from products.models import Product, ProductTranslation
from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklImportStatusSyncFactory,
    MiraklProductFeedFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelFeedItem, SalesChannelViewAssign, SyncRequest


class MiraklProductFeedFactoryTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=None,
            api_key="",
        )
        self.view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="default",
            name="Default",
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            sku="SKU-1",
            active=True,
            type=Product.SIMPLE,
        )
        baker.make(
            ProductTranslation,
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Mirakl Product",
            description="Description",
        )
        self.remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU-1",
        )
        baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )
        self.sync_request = baker.make(
            SyncRequest,
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            sync_type=SyncRequest.TYPE_FEED,
            status=SyncRequest.STATUS_PENDING,
        )

    def test_product_feed_factory_builds_feed_file_and_marks_request_done(self):
        feed = MiraklProductFeedFactory(sales_channel=self.sales_channel).run()

        self.assertIsInstance(feed, MiraklSalesChannelFeed)
        self.assertTrue(feed.file)
        self.assertEqual(feed.items.count(), 1)
        item = feed.items.get()
        self.assertEqual(item.action, SalesChannelFeedItem.ACTION_CREATE)
        self.sync_request.refresh_from_db()
        self.assertEqual(self.sync_request.status, SyncRequest.STATUS_DONE)


class MiraklImportStatusSyncFactoryTests(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret",
        )
        self.feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
        )
        self.product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        baker.make(
            SalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=self.product,
            action=SalesChannelFeedItem.ACTION_CREATE,
            status=SalesChannelFeedItem.STATUS_PENDING,
            payload_data={"rows": [{"sku": "SKU-1", "ean": "123", "prices": [{"price": "10.00"}]}]},
        )
        self.feed.remote_id = "2005"
        self.feed.product_remote_id = "2005"
        self.feed.stage = MiraklSalesChannelFeed.STAGE_PRODUCT
        self.feed.status = MiraklSalesChannelFeed.STATUS_SUBMITTED
        self.feed.save(update_fields=["remote_id", "product_remote_id", "stage", "status"])

    @patch("sales_channels.integrations.mirakl.factories.feeds.status.MiraklOfferSubmitFactory")
    def test_product_import_success_triggers_offer_submit(self, offer_submit_cls):
        factory = MiraklImportStatusSyncFactory(feed=self.feed)

        with patch.object(
            factory,
            "mirakl_get",
            return_value={
                "import_id": 2005,
                "import_status": "COMPLETE",
                "shop_id": 123,
                "transform_lines_in_success": 1,
                "transform_lines_in_error": 0,
            },
        ):
            factory.run()

        self.feed.refresh_from_db()
        self.assertEqual(self.feed.status, self.feed.STATUS_PARTIAL)
        offer_submit_cls.assert_called_once()
