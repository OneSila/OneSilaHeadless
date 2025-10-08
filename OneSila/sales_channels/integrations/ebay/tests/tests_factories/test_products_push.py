from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

from model_bakery import baker

from media.models import Media, MediaProductThrough
from products.models import ProductTranslation
from properties.models import ProductProperty, Property, PropertySelectValue

from sales_channels.integrations.ebay.factories.products.content import (
    EbayProductContentUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.images import (
    EbayMediaProductThroughCreateFactory,
)
from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyUpdateFactory,
)
from sales_channels.integrations.ebay.models import EbayProduct
from sales_channels.integrations.ebay.models.properties import (
    EbayInternalProperty,
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.models.sales_channels import (
    EbayRemoteLanguage,
    EbaySalesChannelView,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign

from .mixins import TestCaseEbayMixin


class EbayProductPushFactoriesTestCase(TestCaseEbayMixin):
    def setUp(self):
        super().setUp()

        self.translate_property_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_translate_property_task"
        )
        self.translate_property_mock = self.translate_property_patcher.start()
        self.translate_property_mock.delay = MagicMock()
        self.addCleanup(self.translate_property_patcher.stop)

        self.translate_select_value_patcher = patch(
            "sales_channels.integrations.ebay.tasks.ebay_translate_select_value_task"
        )
        self.translate_select_value_mock = self.translate_select_value_patcher.start()
        self.translate_select_value_mock.delay = MagicMock()
        self.addCleanup(self.translate_select_value_patcher.stop)

        self.populate_media_title_patcher = patch(
            "media.tasks.populate_media_title_task"
        )
        self.populate_media_title_mock = self.populate_media_title_patcher.start()
        self.populate_media_title_mock.delay = MagicMock()
        self.addCleanup(self.populate_media_title_patcher.stop)

        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            name="UK",
            remote_id="EBAY_GB",
            is_default=True,
            length_unit="CENTIMETER",
            weight_unit="KILOGRAM",
        )
        EbayRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            local_instance="en-us",
            remote_code="en_US",
        )

        self.product = baker.make(
            "products.Product",
            sku="TEST-SKU",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductTranslation.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            language="en-us",
            name="Test Product",
            subtitle="Short subtitle",
            description="Full description",
            short_description="Listing description",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.brand_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.brand_value = baker.make(
            PropertySelectValue,
            property=self.brand_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.brand_product_property = ProductProperty.objects.create(
            product=self.product,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        self.remote_brand = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=self.brand_property,
            localized_name="Brand",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            ebay_property=self.remote_brand,
            local_instance=self.brand_value,
            localized_value="Acme",
        )

        self.weight_property = baker.make(
            Property,
            type=Property.TYPES.FLOAT,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=self.product,
            property=self.weight_property,
            value_float=2.5,
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayInternalProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.weight_property,
            code="packageWeightAndSize__weight__value",
            name="Weight",
            type=Property.TYPES.FLOAT,
            is_root=True,
        )

        self.remote_product = EbayProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_sku="REMOTE-SKU",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            sales_channel_view=self.view,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            remote_id="OFFER-123",
        )

        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
        )
        self.media_through = MediaProductThrough.objects.create(
            product=self.product,
            media=media,
            sort_order=0,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _build_image_factory(self, *, get_value_only: bool) -> EbayMediaProductThroughCreateFactory:
        return EbayMediaProductThroughCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.media_through,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=get_value_only,
        )

    def test_inventory_payload_includes_images_and_properties(self):
        with patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://cdn.example.com/image.jpg"],
        ):
            factory = self._build_image_factory(get_value_only=True)
            payload = factory.build_inventory_payload()

        self.assertEqual(payload["sku"], "REMOTE-SKU")
        self.assertEqual(
            payload["product"]["image_urls"],
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

        availability = payload["availability"]["ship_to_location_availability"]
        self.assertEqual(availability["quantity"], 12)

    def test_create_factory_calls_inventory_api_with_full_payload(self):
        with patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://cdn.example.com/image.jpg"],
        ):
            factory = self._build_image_factory(get_value_only=False)
            expected_payload = factory.build_inventory_payload()

            api = MagicMock()
            factory.api = api
            factory.create_remote()

        api.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        call_kwargs = api.sell_inventory_create_or_replace_inventory_item.call_args.kwargs
        self.assertEqual(call_kwargs["body"], expected_payload)
        self.assertEqual(call_kwargs["content_language"], "en-us".replace("_", "-"))

    def test_content_factory_updates_listing_description(self):
        with patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://cdn.example.com/image.jpg"],
        ):
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
            body={"listing_description": "Listing description"},
            content_language="en-us".replace("_", "-"),
            content_type="application/json",
        )

    def test_property_update_get_value_only_sets_remote_value(self):
        remote_property_instance = EbayProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.brand_product_property,
            remote_product=self.remote_product,
            remote_property=self.remote_brand,
            remote_value="",
        )

        with patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://cdn.example.com/image.jpg"],
        ), patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPushMixin.get_api",
            return_value=MagicMock(),
        ), patch.object(EbayProductProperty, "has_errors", new_callable=PropertyMock, return_value=False):
            factory = EbayProductPropertyUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.brand_product_property,
                remote_product=self.remote_product,
                view=self.view,
                get_value_only=True,
                remote_instance=remote_property_instance,
            )
            factory.log_action = MagicMock()
            factory.log_error = MagicMock()
            factory.run()

        remote_property_instance.refresh_from_db()
        self.assertEqual(remote_property_instance.remote_value, "Acme")
