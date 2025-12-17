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
            multi_tenant_company=self.multi_tenant_company,
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


class FetchRemoteIssuesFactoryStatusTest(TestCase):
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
            remote_sku="SKU-STATUS-123",
            ean_code="EAN123",
        )

    def test_no_asin_defaults_to_pending_approval(self):
        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_PENDING_APPROVAL)

    def test_no_asin_with_issues_sets_approval_rejected_and_persists_on_finalize(self):
        response = {
            "summaries": [],
            "issues": [{"code": "ERR", "message": "Blocked", "severity": "WARNING"}],
        }
        FetchRemoteIssuesFactory(
            remote_product=self.remote_product, view=self.view, response_data=response
        ).run()
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_APPROVAL_REJECTED)

        # Progress updates recompute status normally.
        self.remote_product.set_new_sync_percentage(0)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_PROCESSING)

        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_PENDING_APPROVAL)
