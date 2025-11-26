import json
from unittest.mock import patch, MagicMock
from model_bakery import baker
from core.tests import TransactionTestCase
from currencies.models import Currency
from currencies.currencies import currencies
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductProperty
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_prices.models import SalesPrice
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.models import (
    AmazonPrice,
    AmazonCurrency,
    AmazonProductType,
    AmazonProductBrowseNode,
)
from sales_channels.integrations.amazon.factories.prices.prices import AmazonPriceUpdateFactory


class AmazonPriceTestMixin:
    def prepare_test(self):
        """Populate common objects used across price factory tests."""
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

        self.currency, _ = Currency.objects.get_or_create(
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
            price=80,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )

        self.product_type_property = Property.objects.filter(
            is_product_type=True,
            multi_tenant_company=self.multi_tenant_company,
        ).first()

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
        AmazonProductBrowseNode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            recommended_browse_node_id="1",
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

    def get_patch_value(self, patches, path):
        for patch in patches:
            if patch["path"] == path:
                return patch["value"]
        return None


class AmazonPriceUpdateFactoryTest(DisableWooCommerceSignalsMixin, AmazonPriceTestMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.prepare_test()

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_price_builds_correct_body(self, mock_get_client, mock_listings):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = {
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

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])
        purchasable_offer = self.get_patch_value(patches, "/attributes/purchasable_offer")

        self.assertEqual(body.get("productType"), "CHAIR")
        self.assertEqual(
            purchasable_offer,
            [
                {
                    "audience": "ALL",
                    "currency": "GBP",
                    "marketplace_id": "GB",
                    "our_price": [
                        {
                            "schedule": [{"value_with_tax": 80.0}]
                        }
                    ],
                }
            ],
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.ListingsApi")
    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    def test_update_price_includes_discounted_price(self, mock_get_client, mock_listings):
        """Ensure discounted_price is included when a discount exists."""
        price = SalesPrice.objects.get(product=self.product, currency=self.currency)
        price.rrp = 100
        price.price = 80
        price.save()

        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.return_value = {
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

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        patches = body.get("patches", [])
        purchasable_offer = self.get_patch_value(patches, "/attributes/purchasable_offer")

        discounted = purchasable_offer[0].get("discounted_price")
        self.assertIsNotNone(discounted, "discounted_price is missing")
        schedule = discounted[0]["schedule"][0]
        self.assertEqual(schedule["value_with_tax"], 80.0)
        self.assertIn("start_at", schedule)
        self.assertIn("end_at", schedule)


class AmazonPriceUpdateRequirementsTest(DisableWooCommerceSignalsMixin, TransactionTestCase, AmazonPriceTestMixin):
    """Validate LISTING versus LISTING_OFFER_ONLY logic for price updates."""

    def setUp(self):
        super().setUp()
        self.prepare_test()

    def _run_factory_and_get_body(self):
        with patch(
            "sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client",
            return_value=None,
        ), patch(
            "sales_channels.integrations.amazon.factories.mixins.ListingsApi"
        ) as mock_listings:
            mock_listings.return_value.patch_listings_item.return_value = {
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
            return mock_listings.return_value.patch_listings_item.call_args.kwargs.get(
                "body"
            )

    def test_product_owner_uses_price_listing_requirements(self):
        self.remote_product.product_owner = True
        self.remote_product.save()
        body = self._run_factory_and_get_body()
        patches = body.get("patches", [])

        list_price = self.get_patch_value(patches, "/attributes/list_price")
        self.assertIsNotNone(list_price, "list_price patch is missing")
        self.assertEqual(list_price[0]["value_with_tax"], 80.0)
        self.assertEqual(list_price[0]["marketplace_id"], self.view.remote_id)

    def test_missing_asin_still_uses_listing_requirements(self):
        self.remote_product.product_owner = True
        self.remote_product.save()
        ProductProperty.objects.filter(
            product=self.product,
            property__internal_name="merchant_suggested_asin",
        ).delete()
        body = self._run_factory_and_get_body()
        patches = body.get("patches", [])

        list_price = self.get_patch_value(patches, "/attributes/list_price")
        self.assertIsNotNone(list_price, "list_price patch is missing")
        self.assertEqual(list_price[0]["marketplace_id"], self.view.remote_id)
