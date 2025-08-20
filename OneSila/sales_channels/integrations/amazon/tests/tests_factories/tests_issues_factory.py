from core.tests import TestCase
from model_bakery import baker
from sales_channels.integrations.amazon.factories.sales_channels.issues import FetchRemoteIssuesFactory
from sales_channels.integrations.amazon.models import (
    AmazonExternalProductId,
    AmazonProduct,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)


class FetchRemoteIssuesFactoryExternalIdTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.product = baker.make(
            "products.Product",
            multi_tenant_company=self.multi_tenant_company,
            type="SIMPLE",
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="SKU123",
            ean_code="EAN123",
        )

    def test_updates_existing_external_product_id(self):
        AmazonExternalProductId.objects.create(
            product=self.product,
            view=self.view,
            type=AmazonExternalProductId.TYPE_GTIN,
            value="EAN123",
        )
        response = {"summaries": [{"asin": "ASIN123"}], "issues": []}
        FetchRemoteIssuesFactory(
            remote_product=self.remote_product, view=self.view, response_data=response
        ).run()
        ext = AmazonExternalProductId.objects.get(product=self.product, view=self.view)
        self.assertEqual(ext.created_asin, "ASIN123")

    def test_creates_external_product_id_if_missing(self):
        response = {"summaries": [{"asin": "ASIN999"}], "issues": []}
        FetchRemoteIssuesFactory(
            remote_product=self.remote_product, view=self.view, response_data=response
        ).run()
        ext = AmazonExternalProductId.objects.get(product=self.product, view=self.view)
        self.assertEqual(ext.created_asin, "ASIN999")
        self.assertEqual(ext.value, "ASIN999")
        self.assertEqual(ext.type, AmazonExternalProductId.TYPE_ASIN)
