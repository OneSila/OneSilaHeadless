from django.core.files.base import ContentFile
from model_bakery import baker

from core.tests import TestCase
from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedFileFactory
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklProductType,
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
    MiraklSalesChannelView,
)
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


class MiraklProductFeedFileFactoryTests(DisableMiraklConnectionMixin, TestCase):
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
        self.product_type = baker.make(
            MiraklProductType,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.product_type.template.save(
            "mirakl-template.csv",
            ContentFile("description,sku,description\n"),
            save=True,
        )
        self.feed = baker.make(
            MiraklSalesChannelFeed,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            product_type=self.product_type,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
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
        )
        baker.make(
            MiraklSalesChannelFeedItem,
            multi_tenant_company=self.multi_tenant_company,
            feed=self.feed,
            remote_product=remote_product,
            sales_channel_view=self.view,
            payload_data=[
                {
                    "description": "Product title",
                    "offer__sku": "SKU-1",
                    "offer__description": "Offer description",
                }
            ],
        )

    def test_run_renders_plain_headers_from_namespaced_offer_keys(self):
        MiraklProductFeedFileFactory(feed=self.feed).run()

        with self.feed.file.open("r") as file_handle:
            lines = file_handle.read().splitlines()

        self.assertEqual(lines[0], "description,sku,description")
        self.assertEqual(lines[1], "Product title,SKU-1,Offer description")
