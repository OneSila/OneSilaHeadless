from unittest.mock import patch

from django.test import override_settings
from django.core.files.base import ContentFile
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedSubmitFactory
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelFeed
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductFeedSubmitFactoryTests(DisableMiraklConnectionMixin, TestCase):
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

    @patch("sales_channels.integrations.mirakl.factories.feeds.submit.MiraklProductFeedSubmitFactory.mirakl_post_multipart")
    def test_run_stores_product_import_id_as_remote_id_and_offer_import_separately(self, post_mock):
        post_mock.return_value = {
            "import_id": 2035,
            "product_import_id": 2036,
        }
        feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
        )
        feed.file.save("mirakl.csv", ContentFile("sku;product-id\nSKU-1;SKU-1\n"), save=True)

        MiraklProductFeedSubmitFactory(feed=feed).run()

        feed.refresh_from_db()
        self.assertEqual(feed.status, SalesChannelFeed.STATUS_SUBMITTED)
        self.assertEqual(feed.remote_id, "2036")
        self.assertEqual(feed.product_remote_id, "2036")
        self.assertEqual(feed.offer_import_remote_id, "2035")
        self.assertEqual(feed.offer_remote_id, "")
        self.assertEqual(feed.raw_data["product_submit_response"]["import_id"], 2035)
        self.assertEqual(feed.raw_data["product_submit_response"]["product_import_id"], 2036)
        self.assertEqual(post_mock.call_args.kwargs["path"], "/api/offers/imports")
        self.assertEqual(
            post_mock.call_args.kwargs["payload"],
            {
                "import_mode": "NORMAL",
                "operator_format": "true",
                "with_products": "true",
            },
        )

    @override_settings(DEBUG=True)
    @patch("sales_channels.integrations.mirakl.factories.feeds.submit.MiraklProductFeedSubmitFactory.mirakl_post_multipart")
    def test_run_marks_feed_success_when_debug_skips_upload(self, post_mock):
        view = baker.make(
            MiraklSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="DEFAULT",
        )
        product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
            sku="SKU-1",
        )
        remote_product = baker.make(
            MiraklProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=product,
            remote_sku="SKU-1",
            syncing_current_percentage=100,
            status=MiraklProduct.STATUS_PENDING_APPROVAL,
        )
        feed = baker.make(
            MiraklSalesChannelFeed,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
        )
        item = baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=feed,
            remote_product=remote_product,
            sales_channel_view=view,
            status=MiraklSalesChannelFeedItem.STATUS_PENDING,
        )
        feed.file.save("mirakl.csv", ContentFile("sku;product-id\nSKU-1;SKU-1\n"), save=True)

        MiraklProductFeedSubmitFactory(feed=feed).run()

        feed.refresh_from_db()
        item.refresh_from_db()
        remote_product.refresh_from_db()
        self.assertEqual(feed.status, SalesChannelFeed.STATUS_SUCCESS)
        self.assertEqual(feed.stage, MiraklSalesChannelFeed.STAGE_PRODUCT)
        self.assertEqual(item.status, MiraklSalesChannelFeedItem.STATUS_SUCCESS)
        self.assertEqual(remote_product.status, MiraklProduct.STATUS_COMPLETED)
        self.assertTrue(feed.raw_data["product_submit_skipped"])
        self.assertEqual(
            feed.raw_data["product_submit_skip_reason"],
            "Skipped OF01 upload because settings.DEBUG is True.",
        )
        post_mock.assert_not_called()
