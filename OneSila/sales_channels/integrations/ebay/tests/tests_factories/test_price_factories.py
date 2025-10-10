from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from model_bakery import baker

from currencies.models import Currency
from sales_prices.models import SalesPrice
from sales_channels.integrations.ebay.models.products import EbayPrice

from .mixins import EbayProductPushFactoryTestBase


class EbayPriceUpdateFactoryTest(EbayProductPushFactoryTestBase):
    """Unit tests for the eBay price update factory."""

    def setUp(self) -> None:
        super().setUp()
        self.sales_channel.starting_stock = 5
        self.sales_channel.save(update_fields=["starting_stock"])

        self.currency = Currency.objects.get(iso_code="GBP")
        baker.make(
            "sales_channels.RemoteCurrency",
            sales_channel=self.sales_channel,
            local_instance=self.currency,
            remote_code=self.currency.iso_code,
            multi_tenant_company=self.multi_tenant_company,
        )
        self._set_sales_price(
            currency=self.currency,
            rrp=None,
            price=Decimal("100"),
        )

        self.remote_price = EbayPrice.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            price_data={},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _set_sales_price(self, *, currency, rrp: Decimal | None, price: Decimal | None) -> None:
        SalesPrice.objects.update_or_create(
            product=self.product,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company,
            defaults={"rrp": rrp, "price": price},
        )

    def _build_factory(self, *, get_value_only: bool = False):
        from sales_channels.integrations.ebay.factories.prices import EbayPriceUpdateFactory

        factory = EbayPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_product=self.remote_product,
            view=self.view,
            get_value_only=get_value_only,
        )
        factory.limit_to_currency_iso = self.currency.iso_code
        return factory

    def _prepare_api_mock(self, mock_get_api: MagicMock) -> MagicMock:
        api_mock = MagicMock()
        api_mock.sell_inventory_bulk_update_price_quantity.return_value = {"responses": []}
        mock_get_api.return_value = api_mock
        return api_mock

    def _refresh_price_entry(self) -> Dict[str, Any]:
        self.remote_price.refresh_from_db()
        return self.remote_price.price_data.get(self.currency.iso_code, {})

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    @patch("sales_channels.integrations.ebay.factories.prices.prices.EbayPriceUpdateFactory.get_api")
    def test_bulk_payload_includes_each_currency(self, mock_get_api: MagicMock) -> None:
        second_currency = baker.make(
            "currencies.Currency",
            iso_code="USD",
            name="Dollar",
            symbol="$",
            exchange_rate=1,
            multi_tenant_company=self.multi_tenant_company,
        )
        baker.make(
            "sales_channels.RemoteCurrency",
            sales_channel=self.sales_channel,
            local_instance=second_currency,
            remote_code=second_currency.iso_code,
            multi_tenant_company=self.multi_tenant_company,
        )
        self._set_sales_price(currency=second_currency, rrp=None, price=Decimal("75"))

        api_mock = self._prepare_api_mock(mock_get_api)

        factory = self._build_factory()
        factory.run()

        call_args = api_mock.sell_inventory_bulk_update_price_quantity.call_args
        self.assertIsNotNone(call_args)
        payload = call_args.kwargs.get("body")
        self.assertIsInstance(payload, dict)
        requests = payload.get("requests", [])
        self.assertEqual(len(requests), 1)

        entry = requests[0]
        self.assertEqual(entry.get("offer_id"), "OFFER-123")
        self.assertEqual(entry["price"], {"currency": "GBP", "value": 100.0})
        self.assertEqual(entry.get("available_quantity"), 5)

        api_mock.sell_marketing_create_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_update_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_delete_item_price_markdown_promotion.assert_not_called()

    @patch("sales_channels.integrations.ebay.factories.prices.prices.EbayPriceUpdateFactory.get_api")
    def test_creates_markdown_when_discount_present(self, mock_get_api: MagicMock) -> None:
        self._set_sales_price(currency=self.currency, rrp=Decimal("120"), price=Decimal("95"))

        api_mock = self._prepare_api_mock(mock_get_api)
        api_mock.sell_marketing_create_item_price_markdown_promotion.return_value = {
            "promotionId": "PROMO-NEW",
        }

        factory = self._build_factory()
        factory.run()

        api_mock.sell_marketing_create_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_update_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_delete_item_price_markdown_promotion.assert_not_called()

        entry = self._refresh_price_entry()
        self.assertEqual(entry.get("price"), 120.0)
        self.assertEqual(entry.get("discount_price"), 95.0)
        self.assertIsNone(entry.get("promotion_id"))

    @patch("sales_channels.integrations.ebay.factories.prices.prices.EbayPriceUpdateFactory.get_api")
    def test_updates_markdown_when_discount_changes(self, mock_get_api: MagicMock) -> None:
        self.remote_price.price_data = {
            self.currency.iso_code: {
                "price": 120.0,
                "discount_price": 95.0,
                "promotion_id": "PROMO-EXISTING",
            }
        }
        self.remote_price.save(update_fields=["price_data"])
        self._set_sales_price(currency=self.currency, rrp=Decimal("120"), price=Decimal("88"))

        api_mock = self._prepare_api_mock(mock_get_api)
        api_mock.sell_marketing_update_item_price_markdown_promotion.return_value = {
            "promotion_id": "PROMO-UPDATED",
        }

        factory = self._build_factory()
        factory.run()

        api_mock.sell_marketing_create_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_update_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_delete_item_price_markdown_promotion.assert_not_called()

        entry = self._refresh_price_entry()
        self.assertEqual(entry.get("discount_price"), 88.0)
        self.assertIsNone(entry.get("promotion_id"))

    @patch("sales_channels.integrations.ebay.factories.prices.prices.EbayPriceUpdateFactory.get_api")
    def test_deletes_markdown_when_discount_removed(self, mock_get_api: MagicMock) -> None:
        self.remote_price.price_data = {
            self.currency.iso_code: {
                "price": 120.0,
                "discount_price": 90.0,
                "promotion_id": "PROMO-EXISTING",
            }
        }
        self.remote_price.save(update_fields=["price_data"])
        self._set_sales_price(currency=self.currency, rrp=None, price=Decimal("120"))

        api_mock = self._prepare_api_mock(mock_get_api)

        factory = self._build_factory()
        factory.run()

        api_mock.sell_marketing_create_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_update_item_price_markdown_promotion.assert_not_called()
        api_mock.sell_marketing_delete_item_price_markdown_promotion.assert_not_called()

        entry = self._refresh_price_entry()
        self.assertEqual(entry.get("discount_price"), None)
        self.assertNotIn("promotion_id", entry)

    @patch("sales_channels.integrations.ebay.factories.prices.prices.EbayPriceUpdateFactory.get_api")
    def test_get_value_only_returns_payload(self, mock_get_api: MagicMock) -> None:
        factory = self._build_factory(get_value_only=True)
        factory.run()

        mock_get_api.assert_not_called()
        self.assertIsInstance(factory.value, dict)
        payload = factory.value.get("price_payload")
        self.assertIsInstance(payload, dict)
        self.assertEqual(len(payload.get("requests", [])), 1)
        promotions = factory.value.get("promotions")
        self.assertIsInstance(promotions, list)
