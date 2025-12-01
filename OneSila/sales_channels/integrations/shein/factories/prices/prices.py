from __future__ import annotations

from typing import Any, Dict, List, Optional

from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.models.products import RemotePrice


class SheinPriceUpdateFactory(SheinSignatureMixin, RemotePriceUpdateFactory):
    """Compute Shein price payloads with optional value-only mode."""

    remote_model_class = RemotePrice

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        remote_product,
        api=None,
        currency=None,
        skip_checks: bool = False,
        get_value_only: bool = False,
    ) -> None:
        self.get_value_only = get_value_only
        self.value: Optional[Dict[str, Any]] = None
        self.price_payload: List[Dict[str, Any]] = []
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_product=remote_product,
            api=api,
            currency=currency,
            skip_checks=skip_checks,
        )

    def get_api(self):
        return getattr(self, "api", None)

    def set_api(self) -> None:
        if self.get_value_only:
            return
        super().set_api()

    def get_local_product(self):
        return self.local_instance

    def needs_update(self):
        return bool(self.to_update_currencies)

    def _resolve_currency_code(self, remote_currency: SheinRemoteCurrency) -> Optional[str]:
        if remote_currency.remote_code:
            return remote_currency.remote_code
        if remote_currency.local_instance:
            return remote_currency.local_instance.iso_code
        return None

    def _build_price_info_list(self) -> List[Dict[str, Any]]:
        if not self.to_update_currencies:
            return []

        price_info_list: List[Dict[str, Any]] = []

        remote_currencies = SheinRemoteCurrency.objects.filter(
            sales_channel=self.sales_channel,
            local_instance__iso_code__in=self.to_update_currencies,
        ).select_related("local_instance")

        for remote_currency in remote_currencies:
            iso_code = remote_currency.local_instance.iso_code if remote_currency.local_instance else None
            price_entry = self.price_data.get(iso_code or "", {})

            base_price = price_entry.get("price")
            special_price = price_entry.get("discount_price")

            if base_price is None and special_price is None:
                continue

            entry: Dict[str, Any] = {
                "currency": self._resolve_currency_code(remote_currency),
                "base_price": base_price,
            }
            if special_price is not None:
                entry["special_price"] = special_price

            price_info_list.append(entry)

        return price_info_list

    def _build_product_price_payload(self) -> List[Dict[str, Any]]:
        assigns = SalesChannelViewAssign.objects.filter(
            sales_channel=self.sales_channel,
            product=self.local_instance,
        ).select_related("sales_channel_view")

        product_code = getattr(self.remote_product, "remote_id", None) or self.remote_product.remote_sku
        payload: List[Dict[str, Any]] = []

        for site_entry in assigns:
            site_code = getattr(site_entry.sales_channel_view, "remote_id", None)
            if not site_code:
                continue

            for currency_code, values in self.price_data.items():
                base_price = values.get("price")
                if base_price is None:
                    continue
                entry: Dict[str, Any] = {
                    "currencyCode": currency_code,
                    "productCode": product_code,
                    "site": site_code,
                    "shopPrice": base_price,
                    "specialPrice": values.get("discount_price"),
                    "riseReason": None,
                }
                payload.append(entry)

        return payload

    def update_remote(self):
        price_info_list = self._build_price_info_list()
        self.price_payload = self._build_product_price_payload()

        if self.get_value_only:
            self.value = {"price_info_list": price_info_list}
            return self.value

        if not self.price_payload:
            return {}

        response = self.shein_post(
            path="/open-api/openapi-business-backend/product/price/save",
            payload={"productPriceList": self.price_payload},
        )
        return response.json() if hasattr(response, "json") else {}

    def serialize_response(self, response):
        return response or {}
