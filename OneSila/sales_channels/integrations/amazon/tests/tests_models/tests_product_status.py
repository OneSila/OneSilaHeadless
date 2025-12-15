from core.tests import TestCase
from model_bakery import baker

from sales_channels.integrations.amazon.models import (
    AmazonExternalProductId,
    AmazonProduct,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign


class AmazonProductStatusTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view_gb = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="GB",
        )
        self.view_es = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="ES",
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
            remote_sku="SKU-AMZ-STATUS",
            created_marketplaces=["GB", "ES"],
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view_gb,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view_es,
            remote_product=self.remote_product,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _set_asin(self, *, view, asin: str):
        AmazonExternalProductId.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            view=view,
            type=AmazonExternalProductId.TYPE_ASIN,
            value=asin,
            created_asin=asin,
        )

    def test_completed_when_all_marketplaces_and_asins_ready(self):
        self._set_asin(view=self.view_gb, asin="ASIN-GB")
        self._set_asin(view=self.view_es, asin="ASIN-ES")

        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_COMPLETED)

    def test_partially_listed_when_missing_created_marketplace(self):
        self.remote_product.created_marketplaces = ["GB"]
        self.remote_product.save(update_fields=["created_marketplaces"])
        self._set_asin(view=self.view_gb, asin="ASIN-GB")
        self._set_asin(view=self.view_es, asin="ASIN-ES")

        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_PARTIALLY_LISTED)

    def test_partially_listed_when_missing_asin_for_assigned_view(self):
        self._set_asin(view=self.view_gb, asin="ASIN-GB")

        self.remote_product.set_new_sync_percentage(100)
        self.remote_product.refresh_from_db()
        self.assertEqual(self.remote_product.status, AmazonProduct.STATUS_PARTIALLY_LISTED)

