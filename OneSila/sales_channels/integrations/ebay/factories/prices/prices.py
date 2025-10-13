from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.utils import timezone
from datetime import timedelta

from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models.products import EbayPrice, EbayProductOffer


class EbayPriceUpdateFactory(GetEbayAPIMixin, RemotePriceUpdateFactory):
    """Synchronise eBay offer prices and optional markdown promotions."""

    remote_model_class = EbayPrice

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        remote_product,
        view,
        api=None,
        currency=None,
        skip_checks: bool = False,
        get_value_only: bool = False,
    ) -> None:
        if view is None:
            raise ValueError("EbayPriceUpdateFactory requires a marketplace view instance")

        self.view = view
        self.get_value_only = get_value_only
        self.value: Optional[Dict[str, Any]] = None
        self.previous_price_data: Dict[str, Dict[str, Any]] = {}
        self.limit_to_currency_iso: Optional[str] = None
        self.skip_price_update: bool = False

        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_product=remote_product,
            api=api,
            currency=currency,
            skip_checks=skip_checks,
        )

    # ------------------------------------------------------------------
    # Base overrides
    # ------------------------------------------------------------------
    def get_local_product(self):
        return self.local_instance

    def preflight_check(self) -> bool:
        allowed = super().preflight_check()
        if not allowed:
            return False

        if self.remote_instance:
            self.previous_price_data = dict(self.remote_instance.price_data or {})

        return bool(self.to_update_currencies)

    def set_api(self) -> None:
        """Skip API creation when only computing payload values."""
        if self.get_value_only:
            return
        super().set_api()

    # ------------------------------------------------------------------
    # Remote helpers
    # ------------------------------------------------------------------
    def _get_offer_remote_id(self) -> Optional[str]:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None or self.view is None:
            return None

        offer = (
            EbayProductOffer.objects.filter(
                remote_product=self.remote_product,
                sales_channel_view=self.view,
            )
            .exclude(remote_id__isnull=True)
            .exclude(remote_id="")
            .first()
        )

        if offer:
            return offer.remote_id

        if self.remote_product.is_variation and self.remote_product.remote_parent_product:
            parent_offer = (
                EbayProductOffer.objects.filter(
                    remote_product=self.remote_product.remote_parent_product,
                    sales_channel_view=self.view,
                )
                .exclude(remote_id__isnull=True)
                .exclude(remote_id="")
                .first()
            )
            if parent_offer:
                return parent_offer.remote_id

        return None

    def _get_quantity(self) -> Optional[int]:
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock is None:
            return None

        product = getattr(self.remote_product, "local_instance", None)
        if product is not None:
            if not getattr(product, "active", True):
                return 0
            is_configurable = getattr(product, "is_configurable", None)
            if callable(is_configurable) and is_configurable():
                return 0

        return max(int(starting_stock), 0)

    def _get_language_code(self) -> Optional[str]:
        remote_languages = getattr(self.view, "remote_languages", None)
        if remote_languages is not None:
            remote_language = remote_languages.first()
            if remote_language and remote_language.remote_code:
                return remote_language.remote_code
        language = getattr(self.sales_channel.multi_tenant_company, "language", None)
        if language:
            return language
        return None

    def _get_content_language(self) -> str:
        language_code = self._get_language_code()
        if language_code:
            return language_code.replace("_", "-")
        return "en-US"

    def _get_inventory_sku(self) -> Optional[str]:
        remote_product = getattr(self, "remote_product", None)
        if not remote_product:
            return None
        sku = getattr(remote_product, "remote_sku", None) or getattr(remote_product, "remote_id", None)
        if sku:
            return str(sku)
        local_instance = getattr(remote_product, "local_instance", None)
        return getattr(local_instance, "sku", None)

    def _build_price_request(
        self,
        *,
        offer_id: str,
        currency_code: str,
        price_value: float,
        quantity: Optional[int],
    ) -> Dict[str, Any]:
        request: Dict[str, Any] = {
            "offer_id": offer_id,
            "price": {
                "currency": currency_code,
                "value": price_value,
            },
        }
        if quantity is not None:
            request["available_quantity"] = quantity
        return request

    def _build_markdown_payload(
        self,
        *,
        offer_id: str,
        currency_code: str,
        discount_price: float,
        base_price: float,
        inventory_sku: str,
    ) -> Dict[str, Any]:
        start_time = timezone.now().replace(microsecond=0)
        end_time = start_time + timedelta(days=30)
        amount_off = max(float(base_price) - float(discount_price), 0.0)

        return {
            "description": f"Automated markdown for offer {offer_id}",
            "marketplaceId": getattr(self.view, "remote_id", None),
            "promotionStatus": "SCHEDULED",
            "startDate": start_time.isoformat(),
            "endDate": end_time.isoformat(),
            "selectedInventoryDiscounts": [
                {
                    "discountBenefit": {
                        "amountOffItem": {
                            "currency": currency_code,
                            "value": round(amount_off, 2),
                        },
                        "amountOffOrder": {
                            "currency": currency_code,
                            "value": round(amount_off, 2),
                        },
                    },
                    "inventoryCriterion": {
                        "inventoryCriterionType": "INVENTORY_BY_VALUE",
                        "inventoryItems": [
                            {
                                "inventoryReferenceId": inventory_sku,
                                "inventoryReferenceType": "SKU",
                            },
                        ],
                        "listingIds": [offer_id],
                    },
                }
            ],
        }

    def _extract_promotion_id(self, response: Any) -> Optional[str]:
        if not isinstance(response, dict):
            return None
        return (
            response.get("promotion_id")
            or response.get("promotionId")
            or response.get("id")
        )

    def _handle_markdown_for_currency(
        self,
        *,
        api,
        offer_id: str,
        currency_code: str,
        price_info: Dict[str, Any],
        dry_run: bool,
    ) -> Optional[Dict[str, Any]]:
        # Temporarily disable eBay markdown promotions until full configuration
        # (name, media, percentage vs amount) is supported across integrations.
        return None

    # ------------------------------------------------------------------
    # Update hook
    # ------------------------------------------------------------------
    def update_remote(self):
        offer_id = self._get_offer_remote_id()
        quantity = self._get_quantity()

        requests: List[Dict[str, Any]] = []
        promotions: List[Dict[str, Any]] = []

        for currency_code in self.to_update_currencies:
            price_info = self.price_data.get(currency_code, {})
            price_value = price_info.get("price")
            if price_value is None or offer_id is None:
                continue
            requests.append(
                self._build_price_request(
                    offer_id=offer_id,
                    currency_code=currency_code,
                    price_value=price_value,
                    quantity=quantity,
                )
            )

        payload: Dict[str, Any] = {"requests": requests} if requests else {}

        if self.get_value_only:
            for currency_code in self.to_update_currencies:
                price_info = self.price_data.get(currency_code, {})
                action = self._handle_markdown_for_currency(
                    api=None,
                    offer_id=offer_id,
                    currency_code=currency_code,
                    price_info=price_info,
                    dry_run=True,
                )
                if action:
                    promotions.append(action)

            self.value = {
                "price_payload": payload,
                "promotions": promotions,
            }
            return self.value

        api = getattr(self, "api", None)
        if api is None:
            api = self.get_api()
            self.api = api

        if offer_id is None or not requests or self.skip_price_update:
            self.value = {
                "price_payload": payload,
                "promotions": promotions,
            }
            response = []
        else:
            response = api.sell_inventory_bulk_update_price_quantity(
                body=payload,
                content_type="application/json",
            )

        for currency_code in self.to_update_currencies:
            price_info = self.price_data.get(currency_code, {})
            action = self._handle_markdown_for_currency(
                api=api,
                offer_id=offer_id,
                currency_code=currency_code,
                price_info=price_info,
                dry_run=False,
            )
            if action:
                promotions.append(action)

        self.value = {
            "price_payload": payload,
            "promotions": promotions,
        }
        return response

    def serialize_response(self, response):
        return response or {}
