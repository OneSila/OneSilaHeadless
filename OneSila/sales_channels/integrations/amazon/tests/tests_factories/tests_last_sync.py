from types import SimpleNamespace
from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from products.models import Product
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import (
    AmazonProduct,
    AmazonSalesChannel,
    AmazonSalesChannelView,
)

from ..helpers import DisableWooCommerceSignalsMixin


class DummyFactory(GetAmazonAPIMixin):
    """Minimal factory to invoke mixin methods."""

    def __init__(self, sales_channel, remote_product, view):
        self.sales_channel = sales_channel
        self.remote_product = remote_product
        self.view = view

    def _get_client(self):
        return None

    def _get_issue_locale(self):
        return "en"

    def update_assign_issues(self, *args, **kwargs):
        pass

    def get_identifiers(self):
        return "id", None


class AmazonProductLastSyncTest(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        local_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )
        self.remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=local_product,
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_create_product_updates_last_sync(self, listings_api_cls):
        listings_api_cls.return_value.put_listings_item.return_value = SimpleNamespace()
        fac = DummyFactory(self.sales_channel, self.remote_product, self.view)
        product_type = SimpleNamespace(
            product_type_code="CHAIR", listing_offer_required_properties={}
        )

        fac.create_product("SKU", self.view.remote_id, product_type, {"attr": "val"})

        self.remote_product.refresh_from_db()
        self.assertIsNotNone(self.remote_product.last_sync_at)

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    def test_update_product_updates_last_sync(self, listings_api_cls):
        listings_api_cls.return_value.patch_listings_item.return_value = SimpleNamespace()
        fac = DummyFactory(self.sales_channel, self.remote_product, self.view)
        product_type = SimpleNamespace(product_type_code="CHAIR")

        fac.update_product(
            "SKU",
            self.view.remote_id,
            product_type,
            {"attr": "new"},
            current_attributes={"attr": "old"},
        )

        self.remote_product.refresh_from_db()
        self.assertIsNotNone(self.remote_product.last_sync_at)

