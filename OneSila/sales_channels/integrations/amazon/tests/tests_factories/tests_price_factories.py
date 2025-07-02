import json
from unittest.mock import patch, MagicMock
from model_bakery import baker
from core.tests import TestCase
from currencies.models import Currency
from currencies.currencies import currencies
from sales_prices.models import SalesPrice
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.models import AmazonPrice, AmazonCurrency
from sales_channels.integrations.amazon.factories.prices import AmazonPriceUpdateFactory


class AmazonPriceUpdateFactoryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER123",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            api_region_code="EU_UK",
            remote_id="GB",
        )
        self.currency = Currency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
            **currencies["GB"],
        )
        self.remote_currency = AmazonCurrency.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance=self.currency,
            remote_code=self.currency.iso_code,
        )
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=100,
            price=80,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        # remote type is required in the payload
        self.remote_product.remote_type = "CHAIR"
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        self.remote_price = AmazonPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            price_data={},
        )

    def test_update_factory_builds_correct_body(self):
        factory = AmazonPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
        )
        with patch("spapi.ListingsApi.__init__", return_value=None), patch(
            "spapi.ListingsApi.patch_listings_item", return_value=MagicMock(issues=[]) 
        ):
            factory.run()
        expected = {
            "productType": "CHAIR",
            "requirements": "LISTING",
            "attributes": {
                "list_price": [
                    {"currency": "GBP", "amount": 80.0}
                ],
                "uvp_list_price": [
                    {"currency": "GBP", "amount": 100.0}
                ],
            },
        }
        self.assertEqual(factory.body, expected)
