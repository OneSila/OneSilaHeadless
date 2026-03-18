from unittest.mock import patch

from django.core.files.base import ContentFile
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedSubmitFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed
from sales_channels.models import SalesChannelFeed


class MiraklProductFeedSubmitFactoryTests(TestCase):
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
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
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
