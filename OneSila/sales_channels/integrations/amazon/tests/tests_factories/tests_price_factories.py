import json
from unittest.mock import patch, MagicMock
from model_bakery import baker
from core.tests import TransactionTestCase
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


def setup_price_update_testcase(testcase):
    """Populate common objects used across price factory tests."""
    testcase.sales_channel = AmazonSalesChannel.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        remote_id="SELLER123",
    )

    testcase.view = AmazonSalesChannelView.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        sales_channel=testcase.sales_channel,
        name="UK",
        api_region_code="EU_UK",
        remote_id="GB",
    )

    testcase.currency = Currency.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        is_default_currency=True,
        **currencies["GB"],
    )

    testcase.remote_currency = AmazonCurrency.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        sales_channel=testcase.sales_channel,
        sales_channel_view=testcase.view,
        local_instance=testcase.currency,
        remote_code=testcase.currency.iso_code,
    )

    testcase.product = baker.make(
        "products.Product",
        sku="TESTSKU",
        type="SIMPLE",
        multi_tenant_company=testcase.multi_tenant_company,
    )

    SalesPrice.objects.create(
        product=testcase.product,
        currency=testcase.currency,
        rrp=100,
        price=80,
        multi_tenant_company=testcase.multi_tenant_company,
    )

    testcase.remote_product = AmazonProduct.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        sales_channel=testcase.sales_channel,
        local_instance=testcase.product,
        remote_sku="AMZSKU",
    )

    testcase.product_type_property = Property.objects.filter(
        is_product_type=True,
        multi_tenant_company=testcase.multi_tenant_company,
    ).first()

    testcase.product_type_value = baker.make(
        PropertySelectValue,
        property=testcase.product_type_property,
        multi_tenant_company=testcase.multi_tenant_company,
    )

    PropertySelectValueTranslation.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        propertyselectvalue=testcase.product_type_value,
        language=testcase.multi_tenant_company.language,
        value="Chair",
    )

    testcase.rule = ProductPropertiesRule.objects.filter(
        product_type=testcase.product_type_value,
        multi_tenant_company=testcase.multi_tenant_company,
    ).first()

    ProductProperty.objects.create(
        product=testcase.product,
        property=testcase.product_type_property,
        value_select=testcase.product_type_value,
        multi_tenant_company=testcase.multi_tenant_company,
    )

    AmazonProductType.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        sales_channel=testcase.sales_channel,
        local_instance=testcase.rule,
        product_type_code="CHAIR",
    )

    SalesChannelViewAssign.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        product=testcase.product,
        sales_channel_view=testcase.view,
        sales_channel=testcase.sales_channel,
        remote_product=testcase.remote_product,
    )

    testcase.remote_price = AmazonPrice.objects.create(
        multi_tenant_company=testcase.multi_tenant_company,
        sales_channel=testcase.sales_channel,
        remote_product=testcase.remote_product,
        price_data={},
    )


class AmazonPriceUpdateFactoryTest(TransactionTestCase):
    def setUp(self):
        super().setUp()
        setup_price_update_testcase(self)

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_price_builds_correct_body(self, mock_get_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.return_value = {
            "submissionId": "mock-submission-id",
            "processingStatus": "VALID",
            "status": "VALID",
            "issues": [],
        }
        factory = AmazonPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
        )
        factory.run()

        expected = {
            "productType": "CHAIR",
            "requirements": "LISTING_OFFER_ONLY",
            "attributes": {
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
            },
        }

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertEqual(body, expected)


class AmazonPriceUpdateRequirementsTest(TransactionTestCase):
    """Validate LISTING versus LISTING_OFFER_ONLY logic for price updates."""

    def setUp(self):
        super().setUp()
        setup_price_update_testcase(self)

    def _run_factory_and_get_body(self):
        with patch(
            "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
            return_value=None,
        ), patch(
            "sales_channels.integrations.amazon.factories.mixins.ListingsApi"
        ) as mock_listings:
            mock_listings.return_value.put_listings_item.return_value = {
                "submissionId": "mock-submission-id",
                "processingStatus": "VALID",
                "status": "VALID",
                "issues": [],
            }

            fac = AmazonPriceUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                remote_product=self.remote_product,
                view=self.view,
            )
            fac.run()
            return mock_listings.return_value.put_listings_item.call_args.kwargs.get(
                "body"
            )

    def test_listing_owner_uses_listing_requirements(self):
        self.sales_channel.listing_owner = True
        self.sales_channel.save()
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING")
        self.assertIn("list_price", body["attributes"])

    def test_product_owner_uses_listing_requirements(self):
        self.sales_channel.listing_owner = False
        self.sales_channel.save()
        self.remote_product.product_owner = True
        self.remote_product.save()
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING")
        self.assertIn("list_price", body["attributes"])

    def test_missing_asin_still_uses_listing_requirements(self):
        self.sales_channel.listing_owner = False
        self.sales_channel.save()
        self.remote_product.product_owner = True
        self.remote_product.save()
        ProductProperty.objects.filter(
            product=self.product,
            property__internal_name="merchant_suggested_asin",
        ).delete()
        body = self._run_factory_and_get_body()
        self.assertEqual(body["requirements"], "LISTING")
        self.assertIn("list_price", body["attributes"])
