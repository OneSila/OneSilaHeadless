from __future__ import annotations

from unittest.mock import MagicMock, patch

from sales_channels.integrations.ebay.tests.tests_factories.mixins import (
    EbayProductPushFactoryTestBase,
)


class EbayMediaProductThroughCreateFactoryTest(EbayProductPushFactoryTestBase):
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_inventory_payload_includes_images_and_properties(self, _mock_collect_images):
        factory = self._build_image_factory(get_value_only=True)
        payload = factory.build_inventory_payload()

        self.assertEqual(payload["sku"], "REMOTE-SKU")
        self.assertEqual(
            payload["product"]["imageUrls"],
            ["https://cdn.example.com/image.jpg"],
        )
        self.assertEqual(payload["product"]["aspects"]["Brand"], ["Acme"])
        self.assertEqual(
            payload["packageWeightAndSize"]["weight"]["value"],
            2.5,
        )

    def test_inventory_payload_uses_sales_channel_starting_stock(self):
        self.sales_channel.starting_stock = 12
        self.sales_channel.save(update_fields=["starting_stock"])

        factory = self._build_image_factory(get_value_only=True)
        payload = factory.build_inventory_payload()

        availability = payload["availability"]["shipToLocationAvailability"]
        self.assertEqual(availability["quantity"], 12)

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=["https://cdn.example.com/image.jpg"],
    )
    def test_create_factory_calls_inventory_api_with_full_payload(self, _mock_collect_images):
        factory = self._build_image_factory(get_value_only=False)
        expected_payload = factory.build_inventory_payload()

        api = MagicMock()
        factory.api = api
        factory.create_remote()

        api.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        call_kwargs = api.sell_inventory_create_or_replace_inventory_item.call_args.kwargs
        self.assertEqual(call_kwargs["body"], expected_payload)
        self.assertEqual(call_kwargs["content_language"], "en-us".replace("_", "-"))
