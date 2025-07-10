import json
from unittest.mock import patch, MagicMock
from model_bakery import baker
from core.tests import TestCase
from currencies.models import Currency
from currencies.currencies import currencies
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductProperty
from sales_prices.models import SalesPrice
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.models import AmazonPrice, AmazonCurrency, AmazonProductType
from sales_channels.integrations.amazon.factories.prices.prices import AmazonPriceUpdateFactory


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
        self.product_type_property = Property.objects.filter(is_product_type=True,
                                                             multi_tenant_company=self.multi_tenant_company).first()

        self.product_type_value = baker.make(
            PropertySelectValue,
            property=self.product_type_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=self.product_type_value,
            language=self.multi_tenant_company.language,
            value="Chair",
        )
        self.rule = ProductPropertiesRule.objects.filter(
            product_type=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        ).first()
        ProductProperty.objects.create(
            product=self.product,
            property=self.product_type_property,
            value_select=self.product_type_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="CHAIR",
        )
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

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_factory_builds_correct_body(self, mock_get_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.side_effect = Exception("no amazon")
        mock_instance.get_listings_item.return_value = MagicMock(payload={"attributes": {}})

        factory = AmazonPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
        )
        with self.assertRaises(Exception):
            factory.run()

        expected = {
            "productType": "CHAIR",
            "patches": [
                {
                    "op": "add",
                    "value": [
                        {
                            "purchasable_offer": [
                                {
                                    "audience": "ALL",
                                    "currency": "GBP",
                                    "marketplace_id": "GB",
                                    "our_price": [
                                        {
                                            "schedule": [
                                                {"value_with_tax": 80.0}
                                            ]
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                },
            ],
        }

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        self.assertEqual(body, expected)
