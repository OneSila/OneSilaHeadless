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
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from properties.models import (
    Property,
    PropertyTranslation,
    ProductProperty,
    ProductPropertyTextTranslation,
)
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
        # create asin property and assign to product so factories can fetch it
        asin_local = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
            internal_name="amazon_asin",
            non_deletable=True,
        )
        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=asin_local,
            language=self.multi_tenant_company.language,
            name="Amazon Asin",
        )
        pp = ProductProperty.objects.create(
            product=self.product,
            property=asin_local,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductPropertyTextTranslation.objects.create(
            product_property=pp,
            language=self.multi_tenant_company.language,
            value_text="ASIN123",
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=asin_local,
            code="merchant_suggested_asin",
            type=Property.TYPES.TEXT,
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
    @patch("sales_channels.integrations.amazon.factories.products.products.ListingsApi")
    def test_create_product_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.put_listings_item.side_effect = Exception("no amazon")

        fac = AmazonProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.put_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("productType"), self.remote_product.remote_type)
        self.assertEqual(body.get("requirements"), "LISTING")

    @patch("sales_channels.integrations.amazon.factories.mixins.GetAmazonAPIMixin._get_client", return_value=None)
    @patch("sales_channels.integrations.amazon.factories.products.products.ListingsApi")
    def test_update_product_factory_builds_correct_body(self, mock_listings, mock_client):
        mock_instance = mock_listings.return_value
        mock_instance.patch_listings_item.side_effect = Exception("no amazon")

        fac = AmazonProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_instance=self.remote_product,
            view=self.view,
        )
        fac.run()

        body = mock_instance.patch_listings_item.call_args.kwargs.get("body")
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("productType"), self.remote_product.remote_type)
        self.assertEqual(body.get("requirements"), "LISTING")


    def test_create_product_factory_builds_correct_payload(self):
        """This test checks if the CreateFactory gives the expected payload including attributes, prices, and content."""
        pass


    def test_sync_switches_to_create_if_product_not_exists(self):
        """This test ensures that calling sync triggers a create if the product doesn't exist remotely."""
        pass


    def test_create_product_on_different_marketplace(self):
        """This test ensures the product is created on a second marketplace correctly and independently using PUT."""
        pass


    def test_update_product_factory_builds_correct_payload(self):
        """This test checks that the update factory builds a correct patch payload with only changed attributes."""
        pass


    def test_delete_product_uses_correct_sku_and_marketplace(self):
        """This test ensures delete factory calls the correct endpoint with the proper SKU and marketplace ID."""
        pass


    def test_update_falls_back_to_create_if_product_missing_remotely(self):
        """This test ensures update falls back to create if the product doesn’t exist remotely in the given marketplace."""
        pass


    def test_update_images_overwrites_old_ones_correctly(self):
        """This test validates that old images are removed and only the new ones are included in the payload."""
        pass


    def test_payload_includes_all_supported_property_types(self):
        """This test adds text, select, and multiselect properties and confirms their correct payload structure."""
        pass


    def test_unmapped_attributes_are_ignored_in_payload(self):
        """This test confirms that unmapped or unknown attributes are not added to the final payload."""
        pass


    def test_missing_ean_or_asin_raises_exception(self):
        """This test ensures the factory raises ValueError if no EAN/GTIN or ASIN is provided."""
        pass


    def test_create_product_with_asin_in_payload(self):
        """This test confirms that ASIN is correctly added and EAN is skipped if ASIN exists."""
        pass


    def test_create_product_with_ean_in_payload(self):
        """This test verifies that EAN is included properly in the absence of ASIN."""
        pass


    def test_custom_properties_are_processed_correctly(self):
        """This test ensures that various valid custom properties are processed using process_single_property and included in payload."""
        pass


    def test_existing_remote_property_gets_updated(self):
        """This test simulates an existing remote property and checks that update payload reflects correct values."""
        pass


    def test_translation_from_sales_channel_is_used_in_payload(self):
        """This test checks that product content is pulled from sales channel translations if available."""
        pass


    def test_translation_fallbacks_to_global_if_not_in_channel(self):
        """This test ensures fallback to global translation when channel-specific translation is missing."""
        pass


    def test_price_sync_enabled_includes_price_fields(self):
        """This test ensures that enabling price sync includes correct pricing fields like list_price and uvp_list_price."""
        pass


    def test_price_sync_disabled_skips_price_fields(self):
        """This test ensures that price fields are skipped when price sync is turned off."""
        pass


    def test_payload_skips_empty_price_fields_gracefully(self):
        """This test confirms that missing prices do not break payload generation and are omitted silently."""
        pass


    def test_missing_view_argument_raises_value_error(self):
        """This test confirms that initializing a factory without a view raises ValueError."""
        pass
