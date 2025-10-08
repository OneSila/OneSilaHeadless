from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from model_bakery import baker

from currencies.models import Currency
from sales_prices.models import SalesPrice
from taxes.models import VatRate

from sales_channels.integrations.ebay.factories.products import (
    EbayProductCreateFactory,
    EbayProductDeleteFactory,
    EbayProductSyncFactory,
    EbayProductUpdateFactory,
)
from sales_channels.integrations.ebay.models.properties import EbayProductProperty
from sales_channels.integrations.ebay.models.taxes import EbayCurrency
from sales_channels.models.sales_channels import SalesChannelViewAssign

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

        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        SalesChannelViewAssign.objects.filter(pk=assign.pk).update(remote_id=None)
        assign.refresh_from_db()

        translation = self.product.translations.get(
            sales_channel=self.sales_channel,
            language="en-us",
        )
        translation.name = "X" * 100
        translation.save(update_fields=["name"])

        media = self.media_through.media
        media.image_web_url = "https://example.com/image.jpg"
        media.save(update_fields=["image_web_url"])

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
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayProductContentUpdateFactory.run"
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run"
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
            inventory_payload["product"]["image_urls"],
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
        self.assertEqual(offer_payload["marketplace_id"], "EBAY_GB")
        self.assertEqual(offer_payload["listing_policies"], {
            "fulfillment_policy_id": "FULFILL-1",
            "payment_policy_id": "PAY-1",
            "return_policy_id": "RETURN-1",
        })
        self.assertEqual(offer_payload["listing_duration"], "GTC")
        self.assertEqual(offer_payload["merchant_location_key"], "LOC-1")
        self.assertEqual(
            offer_payload["pricing_summary"],
            {
                "price": {"currency": "GBP", "value": 95.0},
                "original_retail_price": {"currency": "GBP", "value": 120.0},
            },
        )
        self.assertEqual(
            offer_payload["tax"],
            {"apply_tax": True, "vat_percentage": 20.0},
        )

        api_mock.sell_inventory_publish_offer.assert_called_once_with(
            offer_id="NEW-OFFER",
        )

        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        self.assertEqual(assign.remote_id, "NEW-OFFER")

        mock_price_run.assert_called_once()
        mock_ean_run.assert_called_once()
        mock_content_run.assert_called_once()

        brand_remote = EbayProductProperty.objects.get(
            remote_product=self.remote_product,
            local_instance=self.brand_product_property,
        )
        self.assertEqual(brand_remote.remote_value, "Acme")

        weight_remote = EbayProductProperty.objects.get(
            remote_product=self.remote_product,
            local_instance=self.weight_product_property,
        )
        self.assertEqual(weight_remote.remote_value, "2.5")

    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayEanCodeUpdateFactory.run",
        return_value="EAN-VALUE",
    )
    @patch(
        "sales_channels.integrations.ebay.factories.products.products.EbayPriceUpdateFactory.run",
        return_value={"price_payload": {}, "promotions": []},
    )
    def test_get_value_only_returns_payloads(
        self,
        mock_price_run: MagicMock,
        mock_ean_run: MagicMock,
    ) -> None:
        with patch.object(EbayProductCreateFactory, "get_api") as mock_get_api:
            factory = self._build_create_factory(get_value_only=True)
            result = factory.run()

        mock_get_api.assert_not_called()
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called_once()
        self.assertEqual(result["inventory"]["sku"], "TEST-SKU")
        self.assertIn("listing_policies", result["offer"])
        self.assertEqual(result["price"], {"price_payload": {}, "promotions": []})
        self.assertEqual(result["ean"], "EAN-VALUE")
        self.assertIn("listing_description", result["content"])
        property_map = result["properties"]
        self.assertEqual(property_map[str(self.brand_property.id)], "Acme")
        self.assertEqual(property_map[str(self.weight_property.id)], "2.5")
        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        self.assertIsNone(assign.remote_id)

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
        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        SalesChannelViewAssign.objects.filter(pk=assign.pk).update(remote_id="EXISTING")
        assign.refresh_from_db()

        api_mock = MagicMock()
        api_mock.sell_inventory_create_or_replace_inventory_item.return_value = {"sku": "TEST-SKU"}
        api_mock.sell_inventory_create_offer.return_value = {"offerId": "UPDATED"}
        api_mock.sell_inventory_publish_offer.return_value = {"status": "UPDATED"}

        with patch.object(EbayProductUpdateFactory, "get_api", return_value=api_mock):
            factory = self._build_update_factory()
            factory.run()

        api_mock.sell_inventory_create_offer.assert_called_once()
        api_mock.sell_inventory_publish_offer.assert_called_once_with(offer_id="UPDATED")

        assign.refresh_from_db()
        self.assertEqual(assign.remote_id, "UPDATED")
        mock_price_run.assert_called_once()
        mock_ean_run.assert_called_once()
        mock_content_run.assert_called_once()

    def test_delete_flow_removes_offer_and_inventory(self) -> None:
        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        SalesChannelViewAssign.objects.filter(pk=assign.pk).update(remote_id="TO-DELETE")
        assign.refresh_from_db()

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

        assign.refresh_from_db()
        self.assertIsNone(assign.remote_id)

    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductUpdateFactory.run")
    @patch("sales_channels.integrations.ebay.factories.products.products.EbayProductCreateFactory.run")
    def test_sync_dispatches_to_create(self, mock_create_run: MagicMock, mock_update_run: MagicMock) -> None:
        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        SalesChannelViewAssign.objects.filter(pk=assign.pk).update(remote_id=None)
        assign.refresh_from_db()

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
        assign = SalesChannelViewAssign.objects.get(
            product=self.product,
            sales_channel_view=self.view,
        )
        SalesChannelViewAssign.objects.filter(pk=assign.pk).update(remote_id="HAS-OFFER")
        assign.refresh_from_db()

        factory = EbayProductSyncFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            view=self.view,
        )
        factory.run()

        mock_update_run.assert_called_once()
        mock_create_run.assert_not_called()
