from __future__ import annotations

from typing import Any, Dict, List, Optional

from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.models.products import RemotePrice


class SheinPriceUpdateFactory(RemotePriceUpdateFactory):
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

    def update_remote(self):
        price_info_list = self._build_price_info_list()

        if self.get_value_only:
            self.value = {"price_info_list": price_info_list}
            return self.value

        return price_info_list

    def serialize_response(self, response):
        return response or {}
