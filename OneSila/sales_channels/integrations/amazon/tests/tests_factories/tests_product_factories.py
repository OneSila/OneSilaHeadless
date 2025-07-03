from unittest.mock import patch

from model_bakery import baker

from core.tests import TestCase
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.integrations.amazon.models.sales_channels import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonRemoteLanguage,
)
from sales_channels.integrations.amazon.models.products import AmazonProduct
from sales_channels.integrations.amazon.factories.products import (
    AmazonProductCreateFactory,
    AmazonProductUpdateFactory,
)


class AmazonProductFactoriesTest(TestCase):
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
        AmazonRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_code="en",
        )
        self.product = baker.make(
            "products.Product",
            sku="TESTSKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_product = AmazonProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="AMZSKU",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.products.ListingsApi")
    def test_create_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.side_effect = Exception("no amazon")

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )

        with self.assertRaises(Exception):
            fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("productType"), self.remote_product.remote_type)
        self.assertEqual(body.get("requirements"), "LISTING")

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.products.ListingsApi")
    def test_update_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.side_effect = Exception("no amazon")

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )

        with self.assertRaises(Exception):
            fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("productType"), self.remote_product.remote_type)
        self.assertEqual(body.get("requirements"), "LISTING")

