from __future__ import annotations

from unittest.mock import MagicMock, patch

from sales_channels.integrations.ebay.factories.products.content import (
    EbayProductContentUpdateFactory,
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
