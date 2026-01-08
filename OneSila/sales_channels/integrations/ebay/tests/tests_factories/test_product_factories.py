from __future__ import annotations

from decimal import Decimal
import json
from unittest.mock import MagicMock, patch
from typing import Dict

from model_bakery import baker

from currencies.models import Currency
from ebay_rest.api.sell_inventory.rest import ApiException
from products.models import ConfigurableVariation, Product, ProductTranslation
from properties.models import (
    ProductProperty,
    Property,
    ProductPropertiesRuleItem,
    ProductPropertyTextTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
)
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
from sales_channels.integrations.ebay.models import EbayProductCategory
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
        with self.assertRaises(EbayMissingListingPoliciesError):
            factory.run()

    def test_create_flow_errors_when_price_missing_for_view_currency(self) -> None:
        SalesPrice.objects.filter(product=self.product, currency=self.currency).delete()

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
        EbayProductCategory.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id=" 987654 ",
            multi_tenant_company=self.multi_tenant_company,
        )

        factory = self._build_create_factory()
        factory.remote_product = self.remote_product

        self.assertEqual(factory._get_category_id(), "987654")

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
