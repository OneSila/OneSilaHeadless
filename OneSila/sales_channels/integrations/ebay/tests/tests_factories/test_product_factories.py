from __future__ import annotations

from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker

from currencies.models import Currency
from ebay_rest.api.sell_inventory.rest import ApiException
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableVariation, Product, ProductTranslation
from properties.models import (
    ProductProperty,
    Property,
    ProductPropertiesRuleItem,
    ProductPropertyTextTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
from sales_channels.exceptions import PreFlightCheckError
from sales_prices.models import SalesPrice
from taxes.models import VatRate

from sales_channels.integrations.ebay.exceptions import (
    EbayMissingListingPoliciesError,
    EbayResponseException,
)
from sales_channels.integrations.ebay.factories.products import (
    EbayProductCreateFactory,
    EbayProductDeleteFactory,
    EbayProductVariationAddFactory,
    EbayProductSyncFactory,
    EbayProductUpdateFactory,
)
from sales_channels.integrations.ebay.models import (
    EbayProductCategory,
    EbayProductStoreCategory,
    EbayDocumentType,
    EbayRemoteDocument,
    EbayDocumentThroughProduct,
    EbayStoreCategory,
)
from sales_channels.integrations.ebay.models.properties import (
    EbayProductProperty,
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
)
from sales_channels.integrations.ebay.models.taxes import EbayCurrency
from sales_channels.integrations.ebay.models.products import EbayProductOffer, EbayProduct

from .mixins import EbayProductPushFactoryTestBase


class EbaySimpleProductFactoryTest(EbayProductPushFactoryTestBase):
    """Validate end-to-end flows for simple eBay product exports."""

    def setUp(self) -> None:
        super().setUp()
        self.sales_channel.starting_stock = 10
        self.sales_channel.save(update_fields=["starting_stock"])

        self.currency, _ = Currency.objects.update_or_create(
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "iso_code": "GBP",
                "name": "Pound",
                "symbol": "£",
                "exchange_rate": 1,
                "is_default_currency": True,
            },
        )
        EbayCurrency.objects.update_or_create(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            defaults={
                "local_instance": self.currency,
                "remote_code": self.currency.iso_code,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        SalesPrice.objects.update_or_create(
            product=self.product,
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"rrp": Decimal("120"), "price": Decimal("95")},
        )

        vat_rate = baker.make(
            VatRate,
            rate=Decimal("20"),
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product.vat_rate = vat_rate
        self.product.save(update_fields=["vat_rate"])

        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id="FULFILL-1",
            payment_policy_id="PAY-1",
            return_policy_id="RETURN-1",
            merchant_location_key="LOC-1",
        )
        self.view.refresh_from_db()

        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id=None)
        offer.refresh_from_db()

        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id="FULFILL-1",
            payment_policy_id="PAY-1",
            return_policy_id="RETURN-1",
            merchant_location_key="LOC-1",
        )
        self.view.refresh_from_db()

        translation = self.product.translations.get(
            sales_channel=self.sales_channel,
            language="en-us",
        )
        translation.name = "X" * 100
        translation.save(update_fields=["name"])

        self.image_patch = patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://example.com/image.jpg"],
        )
        self.image_patch.start()
        self.addCleanup(self.image_patch.stop)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_create_factory(self, *, get_value_only: bool = False):
        return EbayProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
            get_value_only=get_value_only,
        )

    def _build_update_factory(self, *, get_value_only: bool = False):
        return EbayProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
            get_value_only=get_value_only,
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_identifiers_use_base_factory(self) -> None:
        create_factory = self._build_create_factory()
        update_factory = self._build_update_factory()

        create_identifier, create_fixing = create_factory.get_identifiers()
        update_identifier, update_fixing = update_factory.get_identifiers()

        self.assertTrue(create_identifier.startswith("EbayProductBaseFactory:"))
        self.assertTrue(update_identifier.startswith("EbayProductBaseFactory:"))
        self.assertEqual(create_fixing, "EbayProductBaseFactory:run")
        self.assertEqual(update_fixing, "EbayProductBaseFactory:run")

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
    )
    def test_create_flow_pushes_inventory_offer_and_publish(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
        mock_content_run: MagicMock,
    ) -> None:
        self.ensure_ebay_leaf_category(
            remote_id="555555",
            view=self.view,
            name="Secondary",
        )
        EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id=str(self.ebay_product_type.remote_id),
            secondary_category_id=" 555555 ",
            multi_tenant_company=self.multi_tenant_company,
        )

        api_mock = MagicMock()
        api_mock.sell_inventory_create_or_replace_inventory_item.return_value = {"sku": "TEST-SKU"}
        api_mock.sell_inventory_create_offer.return_value = {"offer_id": "NEW-OFFER"}
        api_mock.sell_inventory_publish_offer.return_value = {"status": "PUBLISHED"}

        with patch.object(EbayProductCreateFactory, "get_api", return_value=api_mock):
            factory = self._build_create_factory()
            result = factory.run()

        self.assertIsInstance(result, dict)

        inventory_call = api_mock.sell_inventory_create_or_replace_inventory_item.call_args
        self.assertIsNotNone(inventory_call)
        inventory_payload = inventory_call.kwargs["body"]
        self.assertEqual(inventory_payload["sku"], "TEST-SKU")
        self.assertEqual(len(inventory_payload["product"]["title"]), 80)
        self.assertEqual(
            inventory_payload["product"]["imageUrls"],
            ["https://example.com/image.jpg"],
        )
        self.assertEqual(
            inventory_payload["product"]["aspects"].get("Brand"),
            ["Acme"],
        )
        self.assertEqual(
            inventory_payload["packageWeightAndSize"]["weight"]["value"],
            2.5,
        )

        offer_call = api_mock.sell_inventory_create_offer.call_args
        self.assertIsNotNone(offer_call)
        offer_payload = offer_call.kwargs["body"]
        self.assertEqual(offer_payload["sku"], "TEST-SKU")
        self.assertEqual(offer_payload["marketplaceId"], "EBAY_GB")
        self.assertEqual(offer_payload["categoryId"], self.ebay_product_type.remote_id)
        self.assertEqual(offer_payload["secondaryCategoryId"], "555555")
        self.assertEqual(offer_payload["listingPolicies"], {
            "fulfillmentPolicyId": "FULFILL-1",
            "paymentPolicyId": "PAY-1",
            "returnPolicyId": "RETURN-1",
        })
        self.assertEqual(offer_payload["listingDuration"], "GTC")
        self.assertEqual(offer_payload["merchantLocationKey"], "LOC-1")
        self.assertEqual(
            offer_payload["pricingSummary"],
            {
                "price": {"currency": "GBP", "value": 95.0},
                "originalRetailPrice": {"currency": "GBP", "value": 120.0},
                "originallySoldForRetailPriceOn": "OFF_EBAY",
            },
        )
        self.assertEqual(
            offer_payload["tax"],
            {"applyTax": True, "vatPercentage": 20.0},
        )

        api_mock.sell_inventory_publish_offer.assert_called_once_with(
            offer_id="NEW-OFFER",
        )

        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        self.assertEqual(offer.remote_id, "NEW-OFFER")

        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()
        mock_content_run.assert_called_once()

    def test_create_flow_errors_when_policies_missing(self) -> None:
        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id=None,
            payment_policy_id=None,
            return_policy_id=None,
        )
        self.view.refresh_from_db()

        factory = self._build_create_factory()
        with self.assertRaises(PreFlightCheckError):
            factory.run()

    def test_create_flow_errors_when_price_missing_for_view_currency(self) -> None:
        SalesPrice.objects.filter(product=self.product, currency=self.currency).delete()

        # don't care about inspector in this test and we don't wanna get InspectorMissingInformationError
        inspector = self.product.inspector
        inspector.delete()

        factory = self._build_create_factory(get_value_only=True)

        with self.assertRaises(EbayResponseException) as exc_info:
            factory.run()

        message = str(exc_info.exception)
        self.assertIn(self.currency.iso_code, message)

    def test_internal_identifier_shapes_follow_expected_format(self) -> None:
        identifier_map = {
            "isbn": (Property.TYPES.TEXT, "9780000000001"),
            "upc": (Property.TYPES.TEXT, "012345678905"),
            "mpn": (Property.TYPES.TEXT, "MPN-123"),
            "epid": (Property.TYPES.TEXT, "EPID-456"),
        }

        for code, (prop_type, value) in identifier_map.items():
            local_property = baker.make(
                Property,
                type=prop_type,
                multi_tenant_company=self.multi_tenant_company,
            )
            product_property = ProductProperty.objects.create(
                product=self.product,
                property=local_property,
                multi_tenant_company=self.multi_tenant_company,
            )
            ProductPropertyTextTranslation.objects.update_or_create(
                product_property=product_property,
                language="en-us",
                defaults={"value_text": value},
            )
            EbayInternalProperty.objects.update_or_create(
                sales_channel=self.sales_channel,
                code=code,
                defaults={
                    "multi_tenant_company": self.multi_tenant_company,
                    "local_instance": local_property,
                    "name": code.upper(),
                    "type": prop_type,
                    "is_root": False,
                },
            )

        factory = self._build_create_factory(get_value_only=True)
        factory.remote_product = self.remote_product

        with patch.object(factory, "_get_ean_value", return_value="4006381333931"):
            payload = factory.build_inventory_payload()

        product_payload = payload.get("product", {})
        self.assertEqual(product_payload.get("ean"), ["4006381333931"])
        self.assertEqual(product_payload.get("isbn"), ["9780000000001"])
        self.assertEqual(product_payload.get("upc"), ["012345678905"])
        self.assertEqual(product_payload.get("mpn"), "MPN-123")
        self.assertEqual(product_payload.get("epid"), "EPID-456")

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run",
        return_value={}
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run",
        return_value={"price_payload": {}, "promotions": []},
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
        return_value=[],
    )
    def test_create_offer_sets_remote_id_on_existing_offer_error(
        self,
        _mock_collect_images,
        _mock_price_run,
        _mock_ean_run,
        _mock_content_run,
    ) -> None:
        api_mock = MagicMock()
        api_mock.sell_inventory_create_or_replace_inventory_item.return_value = {"sku": "TEST-SKU"}

        error = ApiException(status=400, reason="Bad Request")
        error.body = json.dumps(
            {
                "errors": [
                    {
                        "errorId": 25002,
                        "message": "Offer entity already exists.",
                        "parameters": [
                            {"name": "offerId", "value": "9553634010"},
                        ],
                    }
                ]
            }
        )
        api_mock.sell_inventory_create_offer.side_effect = error
        api_mock.sell_inventory_update_offer.return_value = {"offerId": "9553634010"}
        api_mock.sell_inventory_publish_offer.return_value = {"status": "PUBLISHED"}

        with patch.object(EbayProductCreateFactory, "get_api", return_value=api_mock):
            factory = self._build_create_factory()
            factory.run()

        offer_payload = api_mock.sell_inventory_create_offer.call_args.kwargs["body"]
        self.assertEqual(offer_payload.get("categoryId"), self.ebay_product_type.remote_id)
        api_mock.sell_inventory_update_offer.assert_called_once()
        update_call = api_mock.sell_inventory_update_offer.call_args
        self.assertEqual(update_call.kwargs.get("offer_id"), "9553634010")
        self.assertEqual(update_call.kwargs.get("body"), offer_payload)
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        self.assertEqual(offer.remote_id, "9553634010")
        api_mock.sell_inventory_publish_offer.assert_called_once_with(offer_id="9553634010")

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN-VALUE",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run",
        return_value={"price_payload": {}, "promotions": []},
    )
    def test_ean_code_factory_get_value_only_returns_payloads(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
    ) -> None:
        with patch.object(EbayProductCreateFactory, "get_api") as mock_get_api:
            factory = self._build_create_factory(get_value_only=True)
            result = factory.run()

        mock_get_api.assert_not_called()
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()
        self.assertEqual(result["inventory"]["sku"], "TEST-SKU")
        self.assertIn("listingPolicies", result["offer"])
        self.assertEqual(result["offer"].get("categoryId"), self.ebay_product_type.remote_id)
        self.assertEqual(
            result["offer"]["pricingSummary"],
            {
                "price": {"currency": "GBP", "value": 95.0},
                "originalRetailPrice": {"currency": "GBP", "value": 120.0},
                "originallySoldForRetailPriceOn": "OFF_EBAY",
            },
        )
        self.assertEqual(result["price"], {"price_payload": {}, "promotions": []})
        self.assertEqual(result["ean"], "EAN-VALUE")
        self.assertIn("listingDescription", result["content"])
        property_map = result["properties"]

        self.assertEqual(property_map[str(self.brand_property.id)], "Acme")
        self.assertEqual(property_map[str(self.weight_property.id)], "2.5")
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        self.assertIsNone(offer.remote_id)

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN-VALUE",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run",
        return_value={"price_payload": {}, "promotions": []},
    )
    def test_value_only_payload_includes_multiple_remote_mappings_for_same_local_property(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
    ) -> None:
        local_color = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_main_color = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_size = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.SELECT,
        )
        local_width = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )
        local_package_width = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.FLOAT,
        )
        local_not_mapped = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            type=Property.TYPES.TEXT,
        )

        color_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_color,
        )
        size_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=local_size,
        )

        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=local_color,
            value_select=color_value,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=local_size,
            value_select=size_value,
        )
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=local_width,
            value_float=15.75,
        )
        product_property_not_mapped = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property=local_not_mapped,
        )
        ProductPropertyTextTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product_property=product_property_not_mapped,
            language="en-us",
            value_text="ignore-me",
        )

        remote_color = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_color,
            localized_name="Color",
            type=Property.TYPES.SELECT,
        )
        remote_main_color = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_color,
            localized_name="Main Color",
            type=Property.TYPES.SELECT,
        )
        remote_size = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_size,
            localized_name="Size",
            type=Property.TYPES.SELECT,
        )
        EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_width,
            localized_name="Width",
            type=Property.TYPES.FLOAT,
        )
        EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=local_width,
            localized_name="Package Width",
            type=Property.TYPES.FLOAT,
        )
        EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=None,
            localized_name="Not Mapped Remote",
            type=Property.TYPES.TEXT,
        )

        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=remote_color,
            marketplace=self.view,
            local_instance=color_value,
            localized_value="Red-A",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=remote_main_color,
            marketplace=self.view,
            local_instance=color_value,
            localized_value="Red-B",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            ebay_property=remote_size,
            marketplace=self.view,
            local_instance=size_value,
            localized_value="L-A",
        )

        with patch.object(EbayProductCreateFactory, "get_api") as mock_get_api:
            factory = self._build_create_factory(get_value_only=True)
            result = factory.run()

        mock_get_api.assert_not_called()
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()

        aspects = result["inventory"]["product"]["aspects"]
        self.assertEqual(aspects.get("Color"), ["Red-A"])
        self.assertEqual(aspects.get("Main Color"), ["Red-B"])
        self.assertEqual(aspects.get("Size"), ["L-A"])
        self.assertEqual(aspects.get("Width"), ["15.75"])
        self.assertEqual(aspects.get("Package Width"), ["15.75"])
        self.assertNotIn("Not Mapped Remote", aspects)

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
    )
    def test_update_flow_refreshes_offer(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
        mock_content_run: MagicMock,
    ) -> None:
        self.ensure_ebay_leaf_category(
            remote_id="555555",
            view=self.view,
            name="Secondary",
        )
        EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id=str(self.ebay_product_type.remote_id),
            secondary_category_id="555555",
            multi_tenant_company=self.multi_tenant_company,
        )

        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id="EXISTING")
        offer.refresh_from_db()

        api_mock = MagicMock()
        api_mock.sell_inventory_create_or_replace_inventory_item.return_value = {"sku": "TEST-SKU"}
        api_mock.sell_inventory_update_offer.return_value = {"offerId": "UPDATED"}
        api_mock.sell_inventory_publish_offer.return_value = {"status": "UPDATED"}

        with patch.object(EbayProductUpdateFactory, "get_api", return_value=api_mock):
            factory = self._build_update_factory()
            factory.run()

        api_mock.sell_inventory_create_offer.assert_not_called()
        api_mock.sell_inventory_update_offer.assert_called_once()
        update_call = api_mock.sell_inventory_update_offer.call_args
        self.assertEqual(update_call.kwargs.get("offer_id"), "EXISTING")
        self.assertEqual(
            update_call.kwargs.get("body", {}).get("secondaryCategoryId"),
            "555555",
        )
        api_mock.sell_inventory_publish_offer.assert_called_once_with(offer_id="UPDATED")

        offer.refresh_from_db()
        self.assertEqual(offer.remote_id, "UPDATED")
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()
        mock_content_run.assert_called_once()

    def test_get_category_id_prefers_product_category_mapping(self) -> None:
        self.ensure_ebay_leaf_category(
            remote_id="987654",
            view=self.view,
            name="Test",
        )
        self.ensure_ebay_leaf_category(
            remote_id="555555",
            view=self.view,
            name="Secondary",
        )
        EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id=" 987654 ",
            secondary_category_id=" 555555 ",
            multi_tenant_company=self.multi_tenant_company,
        )

        factory = self._build_create_factory()
        factory.remote_product = self.remote_product

        self.assertEqual(factory._get_category_id(), "987654")
        self.assertEqual(factory._get_secondary_category_id(), "555555")

    def test_get_category_id_falls_back_to_product_type(self) -> None:
        factory = self._build_create_factory()
        factory.remote_product = self.remote_product

        self.assertEqual(factory._get_category_id(), str(self.ebay_product_type.remote_id))

    def test_delete_flow_removes_offer_and_inventory(self) -> None:
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id="TO-DELETE")
        offer.refresh_from_db()

        api_mock = MagicMock()
        api_mock.sell_inventory_delete_offer.return_value = {}
        api_mock.sell_inventory_delete_inventory_item.return_value = {}

        with patch.object(EbayProductDeleteFactory, "get_api", return_value=api_mock):
            factory = EbayProductDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            factory.run()

        api_mock.sell_inventory_delete_offer.assert_called_once_with(offer_id="TO-DELETE")
        api_mock.sell_inventory_delete_inventory_item.assert_called_once_with(sku="TEST-SKU")

        self.assertFalse(
            EbayProductOffer.objects.filter(pk=offer.pk).exists()
        )
        self.assertFalse(
            EbayProduct.objects.filter(pk=self.remote_product.pk).exists()
        )

    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductUpdateFactory.run")
    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductCreateFactory.run")
    def test_sync_dispatches_to_create(self, mock_create_run: MagicMock, mock_update_run: MagicMock) -> None:
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id=None)
        offer.refresh_from_db()

        factory = EbayProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        factory.run()

        mock_create_run.assert_called_once()
        mock_update_run.assert_not_called()

    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductUpdateFactory.run")
    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductCreateFactory.run")
    def test_sync_dispatches_to_update(self, mock_create_run: MagicMock, mock_update_run: MagicMock) -> None:
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id="HAS-OFFER")
        offer.refresh_from_db()

        factory = EbayProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        factory.run()

        mock_update_run.assert_called_once()
        mock_create_run.assert_not_called()

    def test_sync_disables_price_update_during_resync(self) -> None:
        offer = EbayProductOffer.objects.get(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )
        EbayProductOffer.objects.filter(pk=offer.pk).update(remote_id="HAS-OFFER")
        offer.refresh_from_db()

        captured: Dict[str, bool] = {}
        original_init = EbayProductUpdateFactory.__init__

        def capture_init(self, *, enable_price_update: bool = True, **kwargs) -> None:
            captured["enable_price_update"] = enable_price_update
            original_init(self, enable_price_update=enable_price_update, **kwargs)

        with patch.object(EbayProductUpdateFactory, "run", MagicMock(return_value=None)):
            with patch.object(EbayProductUpdateFactory, "__init__", capture_init):
                factory = EbayProductSyncFactory(
                    sales_channel=self.sales_channel,
                    local_instance=self.product,
                    view=self.view,
                )
                factory.run()

        self.assertIn("enable_price_update", captured)
        self.assertFalse(captured["enable_price_update"])


class EbayConfigurableProductFactoryTest(EbayProductPushFactoryTestBase):
    """End-to-end coverage for configurable eBay product exports."""

    def setUp(self) -> None:
        super().setUp()
        self.sales_channel.starting_stock = 10
        self.sales_channel.save(update_fields=["starting_stock"])

        self.currency, _ = Currency.objects.update_or_create(
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "iso_code": "GBP",
                "name": "Pound",
                "symbol": "£",
                "exchange_rate": 1,
                "is_default_currency": True,
            },
        )
        EbayCurrency.objects.update_or_create(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            defaults={
                "local_instance": self.currency,
                "remote_code": self.currency.iso_code,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        SalesPrice.objects.update_or_create(
            product=self.product,
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"rrp": Decimal("120"), "price": Decimal("95")},
        )

        vat_rate = baker.make(
            VatRate,
            rate=Decimal("20"),
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product.vat_rate = vat_rate
        self.product.type = Product.CONFIGURABLE
        self.product.save(update_fields=["vat_rate", "type"])

        EbayProductOffer.objects.filter(
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        ).update(remote_id=None)

        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id="FULFILL-1",
            payment_policy_id="PAY-1",
            return_policy_id="RETURN-1",
            merchant_location_key="LOC-1",
        )
        self.view.refresh_from_db()

        self.image_patch = patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._collect_image_urls",
            return_value=["https://example.com/image.jpg"],
        )
        self.image_patch.start()
        self.addCleanup(self.image_patch.stop)

        self.children = [
            self._create_child_product(sku="TEST-SKU-1", name="Child One"),
            self._create_child_product(sku="TEST-SKU-2", name="Child Two"),
        ]

    def _create_child_product(self, *, sku: str, name: str):
        child = baker.make(
            "products.Product",
            sku=sku,
            type=Product.SIMPLE,
            multi_tenant_company=self.multi_tenant_company,
        )
        from products_inspector.models import Inspector

        try:
            inspector = child.inspector
        except Inspector.DoesNotExist:
            inspector = Inspector.objects.create(
                product=child,
                has_missing_information=False,
                has_missing_optional_information=False,
            )
        else:
            inspector.has_missing_information = False
            inspector.has_missing_optional_information = False
            inspector.save(update_fields=["has_missing_information", "has_missing_optional_information"])
        self._assign_product_type(child)
        ProductTranslation.objects.create(
            product=child,
            sales_channel=self.sales_channel,
            language="en-us",
            name=name,
            subtitle="Child subtitle",
            description="Child description",
            short_description="Child short description",
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=child,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )
        ProductProperty.objects.create(
            product=child,
            property=self.weight_property,
            value_float=2.5,
            multi_tenant_company=self.multi_tenant_company,
        )
        child.vat_rate = self.product.vat_rate
        child.save(update_fields=["vat_rate"])
        SalesPrice.objects.update_or_create(
            product=child,
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"rrp": Decimal("120"), "price": Decimal("95")},
        )
        ConfigurableVariation.objects.create(
            parent=self.product,
            variation=child,
            multi_tenant_company=self.multi_tenant_company,
        )
        return child

    @staticmethod
    def _spec_map(*, specifications: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        mapped: Dict[str, List[str]] = {}
        for specification in specifications:
            name = specification.get("name")
            values = specification.get("values", [])
            if isinstance(name, str):
                mapped[name] = list(values) if isinstance(values, list) else []
        return mapped

    def _prime_remote_state(self) -> None:
        api_mock = MagicMock()
        api_mock.sell_inventory_bulk_create_or_replace_inventory_item.return_value = {"responses": []}
        api_mock.sell_inventory_bulk_create_offer.return_value = {
            "responses": [
                {"offerId": f"OFFER-{child.sku}"}
                for child in self.children
            ]
        }
        api_mock.sell_inventory_create_or_replace_inventory_item_group.return_value = {
            "inventory_item_group_key": self.product.sku
        }
        api_mock.sell_inventory_publish_offer_by_inventory_item_group.return_value = {
            "status": "PUBLISHED"
        }

        with patch.object(EbayProductCreateFactory, "get_api", return_value=api_mock), patch(
            "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
        ), patch(
            "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
            return_value="EAN",
        ), patch(
            "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
        ), patch(
            "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._build_varies_by_configuration",
            return_value=None,
        ):
            factory = EbayProductCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            factory.run()

    @patch(
        "sales_channels.integrations.ebay.factories.products.mixins.EbayInventoryItemPayloadMixin._build_varies_by_configuration",
        return_value={
            "aspectsImageVariesBy": ["Size"],
            "specifications": [{"name": "Size", "values": ["Child One", "Child Two"]}],
        },
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
    )
    def test_configurable_create_flow_batches_children_and_group(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
        mock_content_run: MagicMock,
        mock_varies: MagicMock,
    ) -> None:
        api_mock = MagicMock()
        api_mock.sell_inventory_bulk_create_or_replace_inventory_item.return_value = {"responses": []}
        api_mock.sell_inventory_bulk_create_offer.return_value = {
            "responses": [
                {"offerId": "OFFER-TEST-SKU-1"},
                {"offerId": "OFFER-TEST-SKU-2"},
            ]
        }
        api_mock.sell_inventory_create_or_replace_inventory_item_group.return_value = {
            "inventory_item_group_key": self.product.sku
        }
        api_mock.sell_inventory_publish_offer_by_inventory_item_group.return_value = {
            "status": "PUBLISHED"
        }

        with patch.object(EbayProductCreateFactory, "get_api", return_value=api_mock):
            factory = EbayProductCreateFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            result = factory.run()

        inventory_bulk_call = api_mock.sell_inventory_bulk_create_or_replace_inventory_item.call_args
        if inventory_bulk_call is not None:
            inventory_body = inventory_bulk_call.kwargs["body"]
            self.assertEqual(len(inventory_body["requests"]), len(self.children))
            self.assertCountEqual(
                [entry["sku"] for entry in inventory_body["requests"]],
                [child.sku for child in self.children],
            )
        else:
            self.assertEqual(
                api_mock.sell_inventory_create_or_replace_inventory_item.call_count,
                len(self.children),
            )
            child_skus = {
                call.kwargs.get("sku") or call.kwargs.get("body", {}).get("sku")
                for call in api_mock.sell_inventory_create_or_replace_inventory_item.call_args_list
            }
            self.assertSetEqual(child_skus, {child.sku for child in self.children})

        offer_bulk_call = api_mock.sell_inventory_bulk_create_offer.call_args
        if offer_bulk_call is not None:
            offer_body = offer_bulk_call.kwargs["body"]
            self.assertEqual(len(offer_body["requests"]), len(self.children))
            offer_payloads = [entry["offer"] for entry in offer_body["requests"]]
        else:
            self.assertEqual(
                api_mock.sell_inventory_create_offer.call_count,
                len(self.children),
            )
            offer_payloads = [call.kwargs["body"] for call in api_mock.sell_inventory_create_offer.call_args_list]

        for offer in offer_payloads:
            self.assertEqual(offer.get("categoryId"), self.ebay_product_type.remote_id)
            self.assertEqual(offer["listingPolicies"], {
                "fulfillmentPolicyId": "FULFILL-1",
                "paymentPolicyId": "PAY-1",
                "returnPolicyId": "RETURN-1",
            })
            self.assertEqual(
                offer["pricingSummary"],
                {
                    "price": {"currency": "GBP", "value": 95.0},
                    "originalRetailPrice": {"currency": "GBP", "value": 120.0},
                    "originallySoldForRetailPriceOn": "OFF_EBAY",
                },
            )
            self.assertEqual(offer["tax"], {"applyTax": True, "vatPercentage": 20.0})

        group_body = api_mock.sell_inventory_create_or_replace_inventory_item_group.call_args.kwargs["body"]
        self.assertCountEqual(group_body["variantSKUs"], [child.sku for child in self.children])
        self.assertEqual(group_body["variesBy"], mock_varies.return_value)

        publish_body = api_mock.sell_inventory_publish_offer_by_inventory_item_group.call_args.kwargs["body"]
        self.assertEqual(publish_body, {"inventoryItemGroupKey": self.product.sku, "marketplaceId": "EBAY_GB"})


        self.assertIn("children", result)
        self.assertEqual(result["publish"], {"status": "PUBLISHED"})
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()
        mock_content_run.assert_called_once()

    def test_configurable_group_variation_values_use_mapped_select_values(self) -> None:
        size_property = baker.make(
            Property,
            type=Property.TYPES.SELECT,
            multi_tenant_company=self.multi_tenant_company,
        )
        size_large = baker.make(
            PropertySelectValue,
            property=size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        size_medium = baker.make(
            PropertySelectValue,
            property=size_property,
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=size_large,
            language="en-us",
            value="Large",
            multi_tenant_company=self.multi_tenant_company,
        )
        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=size_medium,
            language="en-us",
            value="Medium",
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductPropertiesRuleItem.objects.create(
            rule=self.product_rule,
            property=size_property,
            type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
            multi_tenant_company=self.multi_tenant_company,
        )

        remote_size = EbayProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            local_instance=size_property,
            localized_name="Size",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            ebay_property=remote_size,
            local_instance=size_large,
            remote_id="L",
            localized_value="L",
        )
        EbayPropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            marketplace=self.view,
            ebay_property=remote_size,
            local_instance=size_medium,
            remote_id="M",
            localized_value="M",
        )

        category = self.ensure_ebay_leaf_category(
            remote_id=str(self.category_id),
            view=self.view,
        )
        category.configurator_properties = ["Size"]
        category.save(update_fields=["configurator_properties"])

        ProductProperty.objects.update_or_create(
            product=self.children[0],
            property=size_property,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
                "value_select": size_large,
            },
        )
        ProductProperty.objects.update_or_create(
            product=self.children[1],
            property=size_property,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
                "value_select": size_medium,
            },
        )

        factory = EbayProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
            get_value_only=True,
        )
        factory._resolve_remote_product()
        group_payload = factory._build_inventory_group_payload()

        varies_by = group_payload.get("variesBy") or {}
        specs = varies_by.get("specifications") or []
        size_spec = next(spec for spec in specs if spec.get("name") == "Size")
        self.assertCountEqual(size_spec.get("values", []), ["L", "M"])

    def test_recovery_keeps_size_value_when_other_sku_still_uses_it(self) -> None:
        factory = EbayProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        broken_remote_product = SimpleNamespace(remote_sku="SKU-S-GREEN")
        server_state = {
            "SKU-S-GREEN": {"Size": "S", "Color": "Green"},
            "SKU-S-RED": {"Size": "S", "Color": "Red"},
            "SKU-M-GREEN": {"Size": "M", "Color": "Green"},
            "SKU-M-RED": {"Size": "M", "Color": "Red"},
            "SKU-L-GREEN": {"Size": "L", "Color": "Green"},
            "SKU-L-RED": {"Size": "L", "Color": "Red"},
        }

        with patch.object(
            factory,
            "_fetch_configurator_server_state",
            return_value=(["Size", "Color"], server_state),
        ), patch.object(
            factory,
            "_refresh_variation_state_for_sku",
            return_value={"Size": "Small", "Color": "Green"},
        ) as mock_refresh, patch.object(
            factory,
            "send_inventory_payload",
            return_value={"sku": "SKU-S-GREEN"},
        ) as mock_child_put, patch.object(
            factory,
            "send_inventory_payload_with_variants_override",
            return_value={"status": "OK"},
        ) as mock_group_put:
            responses = factory._recover_configurator_variation_mismatch(
                remote_products=[broken_remote_product],
            )

        self.assertEqual(responses, [{"sku": "SKU-S-GREEN"}])
        self.assertEqual(mock_child_put.call_count, 1)
        self.assertEqual(mock_group_put.call_count, 2)
        mock_refresh.assert_called_once_with(
            sku="SKU-S-GREEN",
            aspect_names=["Size", "Color"],
        )

        first_override = mock_group_put.call_args_list[0].kwargs
        second_override = mock_group_put.call_args_list[1].kwargs

        self.assertNotIn("SKU-S-GREEN", first_override["variant_skus"])
        self.assertCountEqual(
            first_override["variant_skus"],
            ["SKU-S-RED", "SKU-M-GREEN", "SKU-M-RED", "SKU-L-GREEN", "SKU-L-RED"],
        )
        first_spec_map = self._spec_map(specifications=first_override["specifications"])
        self.assertCountEqual(first_spec_map["Size"], ["S", "M", "L"])
        self.assertCountEqual(first_spec_map["Color"], ["Green", "Red"])

        self.assertCountEqual(
            second_override["variant_skus"],
            ["SKU-S-GREEN", "SKU-S-RED", "SKU-M-GREEN", "SKU-M-RED", "SKU-L-GREEN", "SKU-L-RED"],
        )
        second_spec_map = self._spec_map(specifications=second_override["specifications"])
        self.assertCountEqual(second_spec_map["Size"], ["Small", "S", "M", "L"])
        self.assertCountEqual(second_spec_map["Color"], ["Green", "Red"])

    def test_recovery_drops_size_value_when_no_other_sku_uses_it(self) -> None:
        factory = EbayProductUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        broken_remote_product = SimpleNamespace(remote_sku="SKU-S-GREEN")
        server_state = {
            "SKU-S-GREEN": {"Size": "S", "Color": "Green"},
            "SKU-M-GREEN": {"Size": "M", "Color": "Green"},
            "SKU-M-RED": {"Size": "M", "Color": "Red"},
            "SKU-L-GREEN": {"Size": "L", "Color": "Green"},
            "SKU-L-RED": {"Size": "L", "Color": "Red"},
        }

        with patch.object(
            factory,
            "_fetch_configurator_server_state",
            return_value=(["Size", "Color"], server_state),
        ), patch.object(
            factory,
            "_refresh_variation_state_for_sku",
            return_value={"Size": "Small", "Color": "Green"},
        ) as mock_refresh, patch.object(
            factory,
            "send_inventory_payload",
            return_value={"sku": "SKU-S-GREEN"},
        ) as mock_child_put, patch.object(
            factory,
            "send_inventory_payload_with_variants_override",
            return_value={"status": "OK"},
        ) as mock_group_put:
            responses = factory._recover_configurator_variation_mismatch(
                remote_products=[broken_remote_product],
            )

        self.assertEqual(responses, [{"sku": "SKU-S-GREEN"}])
        self.assertEqual(mock_child_put.call_count, 1)
        self.assertEqual(mock_group_put.call_count, 2)
        mock_refresh.assert_called_once_with(
            sku="SKU-S-GREEN",
            aspect_names=["Size", "Color"],
        )

        first_override = mock_group_put.call_args_list[0].kwargs
        second_override = mock_group_put.call_args_list[1].kwargs

        self.assertNotIn("SKU-S-GREEN", first_override["variant_skus"])
        self.assertCountEqual(
            first_override["variant_skus"],
            ["SKU-M-GREEN", "SKU-M-RED", "SKU-L-GREEN", "SKU-L-RED"],
        )
        first_spec_map = self._spec_map(specifications=first_override["specifications"])
        self.assertCountEqual(first_spec_map["Size"], ["M", "L"])
        self.assertCountEqual(first_spec_map["Color"], ["Green", "Red"])

        self.assertCountEqual(
            second_override["variant_skus"],
            ["SKU-S-GREEN", "SKU-M-GREEN", "SKU-M-RED", "SKU-L-GREEN", "SKU-L-RED"],
        )
        second_spec_map = self._spec_map(specifications=second_override["specifications"])
        self.assertCountEqual(second_spec_map["Size"], ["Small", "M", "L"])
        self.assertCountEqual(second_spec_map["Color"], ["Green", "Red"])

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
    )
    def test_configurable_create_value_only_payload(self, mock_price_run: MagicMock, mock_ean_run: MagicMock) -> None:
        factory = EbayProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
            get_value_only=True,
        )
        result = factory.run()

        inventory_batches = result["children"]["inventory"]
        self.assertEqual(len(inventory_batches), 1)
        self.assertEqual(len(inventory_batches[0]["requests"]), 2)
        offer_batches = result["children"]["offers"]
        self.assertEqual(len(offer_batches), 1)
        self.assertEqual(len(offer_batches[0]["requests"]), 2)
        self.assertEqual(result["publish"], {"inventoryItemGroupKey": self.product.sku, "marketplaceId": self.view.remote_id})
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run"
    )
    def test_variation_add_refreshes_group(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
        mock_content_run: MagicMock,
    ) -> None:
        new_child = self._create_child_product(sku="TEST-SKU-3", name="Child Three")
        self.children.append(new_child)

        api_mock = MagicMock()
        api_mock.sell_inventory_create_or_replace_inventory_item.return_value = {"sku": new_child.sku}
        api_mock.sell_inventory_create_offer.return_value = {"offer_id": "OFFER-NEW"}
        api_mock.sell_inventory_publish_offer.return_value = {"status": "PUBLISHED"}
        api_mock.sell_inventory_create_or_replace_inventory_item_group.return_value = {
            "variantSKUs": [child.sku for child in self.children]
        }
        api_mock.sell_inventory_publish_offer_by_inventory_item_group.return_value = {
            "status": "GROUP-PUBLISHED"
        }

        with patch.object(EbayProductVariationAddFactory, "get_api", return_value=api_mock):
            factory = EbayProductVariationAddFactory(
                sales_channel=self.sales_channel,
                local_instance=new_child,
                parent_local_instance=self.product,
                remote_parent_product=self.remote_product,
                view=self.view,
            )
            result = factory.run()

        api_mock.sell_inventory_create_or_replace_inventory_item.assert_called_once()
        api_mock.sell_inventory_create_offer.assert_called_once()
        api_mock.sell_inventory_publish_offer.assert_called_once()
        api_mock.sell_inventory_create_or_replace_inventory_item_group.assert_called_once()
        api_mock.sell_inventory_publish_offer_by_inventory_item_group.assert_called_once()

        remote_new_child = EbayProduct.objects.get(
            local_instance=new_child,
            sales_channel=self.sales_channel,
        )
        offer = EbayProductOffer.objects.get(
            remote_product=remote_new_child,
            sales_channel_view=self.view,
        )
        self.assertEqual(offer.remote_id, "OFFER-NEW")
        self.assertEqual(result["group_publish"], {"status": "GROUP-PUBLISHED"})
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called()
        mock_content_run.assert_called_once()

    def test_configurable_delete_clears_offers_and_group(self) -> None:
        self._prime_remote_state()

        api_mock = MagicMock()
        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.return_value = {
            "status": "WITHDRAWN"
        }
        api_mock.sell_inventory_delete_offer.return_value = {}
        api_mock.sell_inventory_delete_inventory_item_group.return_value = {
            "status": "REMOVED"
        }
        api_mock.sell_inventory_delete_inventory_item.return_value = {}

        with patch.object(EbayProductDeleteFactory, "get_api", return_value=api_mock):
            factory = EbayProductDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            result = factory.run()

        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.assert_called_once()
        api_mock.sell_inventory_delete_inventory_item_group.assert_called_once()

        for child in self.children:
            self.assertFalse(
                EbayProduct.objects.filter(
                    local_instance=child,
                    sales_channel=self.sales_channel,
                ).exists()
            )
            self.assertFalse(
                EbayProductOffer.objects.filter(
                    sales_channel_view=self.view,
                    remote_product__local_instance=child,
                    remote_product__sales_channel=self.sales_channel,
                ).exists()
            )

        self.assertFalse(
            EbayProduct.objects.filter(pk=self.remote_product.pk).exists()
        )
        self.assertEqual(result["withdraw"], {"status": "WITHDRAWN"})

    def test_configurable_delete_ignores_missing_group(self) -> None:
        self._prime_remote_state()

        error_body = json.dumps({
            "errors": [
                {
                    "errorId": 25725,
                    "message": "InventoryItemGroup not found or no offers found for the marketplace.",
                }
            ]
        }).encode("utf-8")
        api_exception = ApiException(status=400, reason="Bad Request")
        api_exception.body = error_body

        api_mock = MagicMock()
        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.side_effect = api_exception
        api_mock.sell_inventory_delete_offer.return_value = {}
        api_mock.sell_inventory_delete_inventory_item_group.return_value = {
            "status": "REMOVED"
        }
        api_mock.sell_inventory_delete_inventory_item.return_value = {}

        with patch.object(EbayProductDeleteFactory, "get_api", return_value=api_mock):
            factory = EbayProductDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            result = factory.run()

        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.assert_called_once()
        api_mock.sell_inventory_delete_inventory_item_group.assert_called_once()

        for child in self.children:
            self.assertFalse(
                EbayProduct.objects.filter(
                    local_instance=child,
                    sales_channel=self.sales_channel,
                ).exists()
            )
            self.assertFalse(
                EbayProductOffer.objects.filter(
                    sales_channel_view=self.view,
                    remote_product__local_instance=child,
                    remote_product__sales_channel=self.sales_channel,
                ).exists()
            )

        self.assertFalse(
            EbayProduct.objects.filter(pk=self.remote_product.pk).exists()
        )
        self.assertEqual(result["withdraw"], {"status": "NOT_FOUND"})

    def test_configurable_delete_ignores_missing_inventory_group(self) -> None:
        self._prime_remote_state()

        error_body = json.dumps({
            "errors": [
                {
                    "errorId": 25705,
                    "message": "The Inventory Item Group named ILFD11000-PARENT could not be found.",
                }
            ]
        }).encode("utf-8")
        api_exception = ApiException(status=404, reason="Not Found")
        api_exception.body = error_body

        api_mock = MagicMock()
        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.return_value = {
            "status": "WITHDRAWN"
        }
        api_mock.sell_inventory_delete_offer.return_value = {}
        api_mock.sell_inventory_delete_inventory_item_group.side_effect = api_exception
        api_mock.sell_inventory_delete_inventory_item.return_value = {}

        with patch.object(EbayProductDeleteFactory, "get_api", return_value=api_mock):
            factory = EbayProductDeleteFactory(
                sales_channel=self.sales_channel,
                local_instance=self.product,
                view=self.view,
            )
            result = factory.run()

        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.assert_called_once()
        api_mock.sell_inventory_delete_inventory_item_group.assert_called_once()

        for child in self.children:
            self.assertFalse(
                EbayProduct.objects.filter(
                    local_instance=child,
                    sales_channel=self.sales_channel,
                ).exists()
            )
            self.assertFalse(
                EbayProductOffer.objects.filter(
                    sales_channel_view=self.view,
                    remote_product__local_instance=child,
                    remote_product__sales_channel=self.sales_channel,
                ).exists()
            )

        self.assertFalse(
            EbayProduct.objects.filter(pk=self.remote_product.pk).exists()
        )
        self.assertEqual(result["group"], {"status": "NOT_FOUND"})

    def test_configurable_delete_collects_child_errors(self) -> None:
        self._prime_remote_state()

        api_mock = MagicMock()
        api_mock.sell_inventory_withdraw_offer_by_inventory_item_group.return_value = {
            "status": "WITHDRAWN"
        }
        api_mock.sell_inventory_delete_inventory_item_group.return_value = {
            "status": "REMOVED"
        }
        api_mock.sell_inventory_delete_inventory_item.return_value = {}

        offer_error = EbayResponseException("Offer delete failed")

        with patch.object(EbayProductDeleteFactory, "get_api", return_value=api_mock):
            with patch.object(EbayProductDeleteFactory, "delete_offer", side_effect=[offer_error, {}]):
                with patch(
                    "sales_channels.integrations.ebay.factories.products.products.logger"
                ) as logger_mock:
                    factory = EbayProductDeleteFactory(
                        sales_channel=self.sales_channel,
                        local_instance=self.product,
                        view=self.view,
                    )
                    result = factory.run()

        self.assertEqual(result["children"]["offers"][0]["error"], "Offer delete failed")
        self.assertEqual(result["children"]["offers"][1], {})
        logger_mock.error.assert_called_once()


class EbayOfferDocumentPayloadFactoryTest(EbayProductPushFactoryTestBase):
    def setUp(self) -> None:
        super().setUp()
        self._fqdn_patcher = patch(
            "get_absolute_url.helpers.get_fqdn",
            return_value="localhost",
        )
        self._fqdn_patcher.start()
        self.addCleanup(self._fqdn_patcher.stop)

        self.currency, _ = Currency.objects.update_or_create(
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "iso_code": "GBP",
                "name": "Pound",
                "symbol": "£",
                "exchange_rate": 1,
                "is_default_currency": True,
            },
        )
        EbayCurrency.objects.update_or_create(
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            defaults={
                "local_instance": self.currency,
                "remote_code": self.currency.iso_code,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        SalesPrice.objects.update_or_create(
            product=self.product,
            currency=self.currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"rrp": Decimal("120"), "price": Decimal("95")},
        )

        vat_rate = baker.make(
            VatRate,
            rate=Decimal("20"),
            multi_tenant_company=self.multi_tenant_company,
        )
        self.product.vat_rate = vat_rate
        self.product.save(update_fields=["vat_rate"])

        type(self.view).objects.filter(pk=self.view.pk).update(
            fulfillment_policy_id="FULFILL-1",
            payment_policy_id="PAY-1",
            return_policy_id="RETURN-1",
            merchant_location_key="LOC-1",
        )
        self.view.refresh_from_db()

    def _build_create_factory(self, *, get_value_only: bool = False):
        return EbayProductCreateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
            get_value_only=get_value_only,
        )

    def _create_mapped_document_assignment(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str,
        language: str = "en",
        remote_document_type_code: str = "USER_GUIDE_OR_MANUAL",
    ):
        document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Public Safety Document",
        )
        ebay_document_type = EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_document_type_code,
            name=remote_document_type_code.title(),
            local_instance=document_type,
        )

        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            file=SimpleUploadedFile(
                name=filename,
                content=content,
                content_type=content_type,
            ),
            document_type=document_type,
            document_language=language,
        )
        media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=media,
        )
        return media_through, ebay_document_type

    def _create_unmapped_document_assignment(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str,
        language: str = "en",
    ):
        document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Unmapped Public Document",
        )
        media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            file=SimpleUploadedFile(
                name=filename,
                content=content,
                content_type=content_type,
            ),
            document_type=document_type,
            document_language=language,
        )
        return MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=media,
        )

    def _build_offer_payload(self, *, api_mock: MagicMock):
        factory = self._build_create_factory(get_value_only=False)
        factory.remote_product = self.remote_product
        factory.api = api_mock
        return factory.build_offer_payload()

    @staticmethod
    def _accept_wait_side_effect(*args, **kwargs):
        remote_document = kwargs["remote_document"]
        remote_document.status = EbayRemoteDocument.STATUS_ACCEPTED
        remote_document.save(update_fields=["status"])
        return remote_document

    def test_offer_payload_includes_regulatory_documents(self) -> None:
        """
        Real scenario:
        A mapped public document is present and accepted by eBay, so regulatory.documents must contain it.
        """
        media_through, ebay_document_type = self._create_mapped_document_assignment(
            filename="safety-sheet.pdf",
            content=b"%PDF-1.4 test content",
            content_type="application/pdf",
            language="de",
            remote_document_type_code="SAFETY_DATA_SHEET",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-100"}
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ) as wait_mock:
            payload = self._build_offer_payload(api_mock=api_mock)

        self.assertEqual(payload["regulatory"]["documents"], [{"documentId": "DOC-100"}])
        wait_mock.assert_called_once()

        create_call = api_mock.commerce_media_create_document_from_url.call_args
        self.assertEqual(create_call.kwargs["content_type"], "application/json")
        self.assertEqual(create_call.kwargs["body"]["documentType"], ebay_document_type.remote_id)
        self.assertEqual(create_call.kwargs["body"]["languages"], ["GERMAN"])
        self.assertIn("http", create_call.kwargs["body"]["documentUrl"])
        api_mock.commerce_media_get_document.assert_not_called()

        remote_document = EbayRemoteDocument.objects.get(
            local_instance=media_through.media,
            sales_channel=self.sales_channel,
            remote_document_type=ebay_document_type,
        )
        self.assertEqual(remote_document.remote_id, "DOC-100")
        self.assertEqual(remote_document.status, EbayRemoteDocument.STATUS_ACCEPTED)
        remote_association = EbayDocumentThroughProduct.objects.get(
            local_instance=media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
            sales_channel=self.sales_channel,
        )
        self.assertEqual(remote_association.remote_url, create_call.kwargs["body"]["documentUrl"])

    def test_offer_payload_raises_for_rejected_documents(self) -> None:
        """
        Real scenario:
        eBay returns REJECTED during status processing, so product push must fail with PreFlightCheckError.
        """
        self._create_mapped_document_assignment(
            filename="manual.pdf",
            content=b"%PDF-1.4 test content",
            content_type="application/pdf",
            language="en",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-REJECTED"}

        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=PreFlightCheckError("Document status is REJECTED."),
        ):
            with self.assertRaises(PreFlightCheckError) as exc:
                self._build_offer_payload(api_mock=api_mock)

        self.assertIn("REJECTED", str(exc.exception))

    def test_offer_payload_raises_for_expired_documents(self) -> None:
        """
        Real scenario:
        eBay returns EXPIRED during status processing, so product push must fail with PreFlightCheckError.
        """
        self._create_mapped_document_assignment(
            filename="manual-expired.pdf",
            content=b"%PDF-1.4 test content",
            content_type="application/pdf",
            language="en",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-EXPIRED"}

        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=PreFlightCheckError("Document status is EXPIRED."),
        ):
            with self.assertRaises(PreFlightCheckError) as exc:
                self._build_offer_payload(api_mock=api_mock)

        self.assertIn("EXPIRED", str(exc.exception))

    def test_offer_payload_raises_when_pending_for_too_long(self) -> None:
        """
        Real scenario:
        eBay keeps the document in pending state past retry limit, so we fail early and ask for retry later.
        """
        self._create_mapped_document_assignment(
            filename="manual-pending.pdf",
            content=b"%PDF-1.4 test content",
            content_type="application/pdf",
            language="en",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-PENDING"}

        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=PreFlightCheckError("Document is still processing on eBay (SUBMITTED)."),
        ):
            with self.assertRaises(PreFlightCheckError) as exc:
                self._build_offer_payload(api_mock=api_mock)

        self.assertIn("processing", str(exc.exception).lower())

    def test_offer_payload_skips_unmapped_document_types(self) -> None:
        """
        Real scenario:
        Product has multiple public documents but only one local type is mapped to eBay; unmapped docs are silently skipped.
        """
        mapped_media_through, _ = self._create_mapped_document_assignment(
            filename="mapped.pdf",
            content=b"%PDF-1.4 mapped",
            content_type="application/pdf",
            language="en",
            remote_document_type_code="USER_GUIDE_OR_MANUAL",
        )
        unmapped_media_through = self._create_unmapped_document_assignment(
            filename="unmapped.pdf",
            content=b"%PDF-1.4 unmapped",
            content_type="application/pdf",
            language="en",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-MAPPED"}
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ):
            payload = self._build_offer_payload(api_mock=api_mock)

        self.assertEqual(payload["regulatory"]["documents"], [{"documentId": "DOC-MAPPED"}])
        self.assertTrue(
            EbayRemoteDocument.objects.filter(
                local_instance=mapped_media_through.media,
                sales_channel=self.sales_channel,
            ).exists()
        )
        self.assertFalse(
            EbayRemoteDocument.objects.filter(
                local_instance=unmapped_media_through.media,
                sales_channel=self.sales_channel,
            ).exists()
        )
        self.assertFalse(
            EbayDocumentThroughProduct.objects.filter(
                local_instance=unmapped_media_through,
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            ).exists()
        )

    def test_offer_payload_pending_remote_document_is_rechecked_and_accepted(self) -> None:
        """
        Real scenario:
        Remote document already exists in pending status; next sync rechecks it and proceeds once accepted.
        """
        media_through, ebay_document_type = self._create_mapped_document_assignment(
            filename="pending-existing.pdf",
            content=b"%PDF-1.4 pending",
            content_type="application/pdf",
            language="en",
        )
        remote_document = EbayRemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through.media,
            remote_document_type=ebay_document_type,
            remote_id="DOC-PENDING-EXISTING",
            status=EbayRemoteDocument.STATUS_SUBMITTED,
        )
        EbayDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
        )

        api_mock = MagicMock()
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ) as wait_mock:
            payload = self._build_offer_payload(api_mock=api_mock)

        self.assertEqual(payload["regulatory"]["documents"], [{"documentId": "DOC-PENDING-EXISTING"}])
        wait_mock.assert_called_once()
        api_mock.commerce_media_create_document_from_url.assert_not_called()
        remote_document.refresh_from_db()
        self.assertEqual(remote_document.status, EbayRemoteDocument.STATUS_ACCEPTED)

    def test_offer_payload_recreates_remote_when_local_row_has_no_remote_id(self) -> None:
        """
        Real scenario:
        Local remote-document row exists but remote_id is empty; sync retries remote creation and then continues.
        """
        media_through, ebay_document_type = self._create_mapped_document_assignment(
            filename="missing-id.pdf",
            content=b"%PDF-1.4 no id",
            content_type="application/pdf",
            language="en",
        )
        remote_document = EbayRemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through.media,
            remote_document_type=ebay_document_type,
            remote_id="",
            status=EbayRemoteDocument.STATUS_PENDING_UPLOAD,
        )
        EbayDocumentThroughProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through,
            remote_product=self.remote_product,
            remote_document=remote_document,
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.return_value = {"documentId": "DOC-RECREATED"}
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ):
            payload = self._build_offer_payload(api_mock=api_mock)

        self.assertEqual(payload["regulatory"]["documents"], [{"documentId": "DOC-RECREATED"}])
        remote_document.refresh_from_db()
        self.assertEqual(remote_document.remote_id, "DOC-RECREATED")
        self.assertEqual(remote_document.status, EbayRemoteDocument.STATUS_ACCEPTED)
        api_mock.commerce_media_create_document_from_url.assert_called_once()

    def test_offer_payload_creates_missing_assign_when_remote_document_exists(self) -> None:
        """
        Real scenario:
        Remote document exists for media but product-association row is missing; sync must create association and include document.
        """
        media_through, ebay_document_type = self._create_mapped_document_assignment(
            filename="existing-doc-no-assign.pdf",
            content=b"%PDF-1.4 existing doc",
            content_type="application/pdf",
            language="en",
        )
        remote_document = EbayRemoteDocument.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=media_through.media,
            remote_document_type=ebay_document_type,
            remote_id="DOC-EXISTS-NO-ASSIGN",
            status=EbayRemoteDocument.STATUS_ACCEPTED,
        )

        api_mock = MagicMock()
        payload = self._build_offer_payload(api_mock=api_mock)

        self.assertEqual(payload["regulatory"]["documents"], [{"documentId": "DOC-EXISTS-NO-ASSIGN"}])
        self.assertTrue(
            EbayDocumentThroughProduct.objects.filter(
                local_instance=media_through,
                remote_product=self.remote_product,
                remote_document=remote_document,
                sales_channel=self.sales_channel,
            ).exists()
        )
        api_mock.commerce_media_create_document_from_url.assert_not_called()

    def test_offer_payload_includes_two_documents_when_two_types_are_mapped(self) -> None:
        """
        Real scenario:
        Product has two mapped document types; both accepted documents must be included in regulatory payload.
        """
        self._create_mapped_document_assignment(
            filename="guide.pdf",
            content=b"%PDF-1.4 guide",
            content_type="application/pdf",
            language="en",
            remote_document_type_code="USER_GUIDE_OR_MANUAL",
        )
        self._create_mapped_document_assignment(
            filename="safety.pdf",
            content=b"%PDF-1.4 safety",
            content_type="application/pdf",
            language="en",
            remote_document_type_code="SAFETY_DATA_SHEET",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.side_effect = [
            {"documentId": "DOC-1"},
            {"documentId": "DOC-2"},
        ]
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ):
            payload = self._build_offer_payload(api_mock=api_mock)

        documents = payload["regulatory"]["documents"]
        self.assertEqual(len(documents), 2)
        self.assertEqual({item["documentId"] for item in documents}, {"DOC-1", "DOC-2"})

    def test_offer_payload_reflects_local_media_through_deletion(self) -> None:
        """
        Real scenario:
        Two mapped documents were synced, then one local MediaProductThrough is deleted; next payload must only include remaining one.
        """
        _, _ = self._create_mapped_document_assignment(
            filename="first.pdf",
            content=b"%PDF-1.4 first",
            content_type="application/pdf",
            language="en",
            remote_document_type_code="USER_GUIDE_OR_MANUAL",
        )
        media_through_to_delete, _ = self._create_mapped_document_assignment(
            filename="second.pdf",
            content=b"%PDF-1.4 second",
            content_type="application/pdf",
            language="en",
            remote_document_type_code="SAFETY_DATA_SHEET",
        )

        api_mock = MagicMock()
        api_mock.commerce_media_create_document_from_url.side_effect = [
            {"documentId": "DOC-FIRST"},
            {"documentId": "DOC-SECOND"},
        ]
        with patch(
            "sales_channels.integrations.ebay.factories.products.documents."
            "EbayRemoteDocumentFactoryBase._wait_until_document_is_accepted",
            side_effect=self._accept_wait_side_effect,
        ):
            initial_payload = self._build_offer_payload(api_mock=api_mock)
        self.assertEqual(len(initial_payload["regulatory"]["documents"]), 2)

        media_through_to_delete.delete()

        payload_after_delete = self._build_offer_payload(api_mock=api_mock)
        self.assertEqual(len(payload_after_delete["regulatory"]["documents"]), 1)
        self.assertEqual(
            {item["documentId"] for item in payload_after_delete["regulatory"]["documents"]},
            {"DOC-FIRST"},
        )

    def test_offer_payload_raises_for_unsupported_document_extension(self) -> None:
        """
        Real scenario:
        A mapped document uses unsupported file extension for eBay media endpoint, so preflight must fail before upload.
        """
        self._create_mapped_document_assignment(
            filename="safety-data.xlsx",
            content=b"spreadsheet",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            language="en",
        )

        api_mock = MagicMock()

        factory = self._build_create_factory(get_value_only=False)
        factory.remote_product = self.remote_product
        factory.api = api_mock

        with self.assertRaises(PreFlightCheckError) as exc:
            self._build_offer_payload(api_mock=api_mock)

        self.assertIn("unsupported file type", str(exc.exception).lower())
        api_mock.commerce_media_create_document_from_url.assert_not_called()

    def test_offer_payload_includes_store_category_names(self) -> None:
        fashion = EbayStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="100",
            name="Fashion",
            order=0,
            level=1,
            is_leaf=False,
        )
        men = EbayStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="101",
            name="Men",
            order=0,
            level=2,
            parent=fashion,
            is_leaf=False,
        )
        shirts = EbayStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="102",
            name="Shirts",
            order=0,
            level=3,
            parent=men,
            is_leaf=True,
        )
        accessories = EbayStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="103",
            name="Accessories",
            order=1,
            level=3,
            parent=men,
            is_leaf=True,
        )
        EbayProductStoreCategory.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            primary_store_category=shirts,
            secondary_store_category=accessories,
        )

        payload = self._build_offer_payload(api_mock=MagicMock())

        self.assertEqual(
            payload.get("storeCategoryNames"),
            ["/Fashion/Men/Shirts", "/Fashion/Men/Accessories"],
        )

    def test_offer_payload_omits_store_category_names_without_mapping(self) -> None:
        payload = self._build_offer_payload(api_mock=MagicMock())
        self.assertNotIn("storeCategoryNames", payload)
