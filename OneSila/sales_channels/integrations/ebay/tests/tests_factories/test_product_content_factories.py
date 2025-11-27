from __future__ import annotations

from unittest.mock import MagicMock, patch

from products.models import ProductTranslation

from sales_channels.integrations.ebay.factories.products.content import (
    EbayProductContentUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.mixins import (
    _FALLBACK_DESCRIPTION_LIMIT,
)
from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)
from sales_channels.models.sales_channels import SalesChannelContentTemplate


class EbayProductContentUpdateFactoryTest(EbayProductPushFactoryTestBase):
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_updates_listing_description(self, _mock_collect_images):
        factory = EbayProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=False,
        )
        factory.build_inventory_payload()

        api = MagicMock()
        factory.api = api
        factory.update_remote()

        api.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        api.sell_inventory_update_offer.assert_called_once_with(
            offer_id="OFFER-123",
            body={"listingDescription": "Listing description"},
            content_language="en-us".replace("_", "-"),
            content_type="application/json",
        )

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_updates_listing_description_with_content_template(self, _mock_collect_images):
        SalesChannelContentTemplate.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            language="en-us",
            template="{{ content }} -- {{ title }}",
        )

        factory = EbayProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=False,
        )
        payload = factory.build_inventory_payload(is_parent=True)

        expected_description = "Full description -- Test Product"
        self.assertEqual(payload["product"]["description"], expected_description)

        api = MagicMock()
        factory.api = api
        factory.update_remote()

        api.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        create_call = api.sell_inventory_create_or_replace_inventory_item.call_args
        create_payload = create_call.kwargs["body"]

        api.sell_inventory_update_offer.assert_called_once_with(
            offer_id="OFFER-123",
            body={"listingDescription": expected_description},
            content_language="en-us".replace("_", "-"),
            content_type="application/json",
        )

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_simple_product_description_keeps_html_when_under_limit(self, _mock_collect_images):
        translation = ProductTranslation.objects.get(
            product=self.product,
            language="en-us",
        )
        description = '<div class="wrapper"><p>Test&nbsp;123</p></div>'
        translation.description = description
        translation.save(update_fields=["description"])

        factory = EbayProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=False,
        )
        payload = factory.build_inventory_payload(is_parent=False)

        self.assertEqual(payload["product"]["description"], description)

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_simple_product_description_strips_html_when_over_limit(self, _mock_collect_images):
        translation = ProductTranslation.objects.get(
            product=self.product,
            language="en-us",
        )
        pattern = '<div class="wrapper"><p>Test&nbsp;123</p></div>'
        repeats = (_FALLBACK_DESCRIPTION_LIMIT // len("Test 123")) + 10
        long_description = pattern * repeats
        translation.description = long_description
        translation.save(update_fields=["description"])

        factory = EbayProductContentUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=False,
        )
        payload = factory.build_inventory_payload(is_parent=False)

        cleaned_description = payload["product"]["description"]
        self.assertEqual(len(cleaned_description), _FALLBACK_DESCRIPTION_LIMIT)
        self.assertNotIn("<", cleaned_description)
        self.assertTrue(cleaned_description.startswith("Test 123"))
