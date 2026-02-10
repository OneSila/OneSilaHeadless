from unittest.mock import patch

from core.tests import TransactionTestCase
from products.models import Product
from sales_channels.exceptions import InspectorMissingInformationError
from sales_channels.integrations.ebay.factories.products.products import EbayProductUpdateFactory
from sales_channels.integrations.ebay.models import EbayProduct, EbaySalesChannelView
from sales_channels.integrations.ebay.tests.tests_factories.mixins import TestCaseEbayMixin


class EbayProductSuccessfullyCreatedTests(TestCaseEbayMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_GB",
            name="UK",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="EBAY-SYNC-1",
        )
        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="EBAY-SYNC-1",
            remote_sku="EBAY-SYNC-1",
            successfully_created=True,
        )

    def test_sets_successfully_created_false_on_validation_error(self):
        factory = EbayProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
            api=None,
            get_value_only=True,
            enable_price_update=False,
        )

        with (
            patch.object(factory, "set_api"),
            patch.object(factory, "set_type"),
            patch.object(factory, "_build_listing_policies"),
            patch.object(factory, "_resolve_remote_product", return_value=self.remote_product),
            patch.object(factory, "validate", side_effect=InspectorMissingInformationError("Missing info")),
        ):
            with self.assertRaises(InspectorMissingInformationError):
                factory.run()

        self.remote_product.refresh_from_db()
        self.assertFalse(self.remote_product.successfully_created)
