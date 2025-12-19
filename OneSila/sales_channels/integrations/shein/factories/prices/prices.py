from __future__ import annotations

from typing import Any, Dict, List, Optional

from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.models.products import RemotePrice
from sales_channels.exceptions import PreFlightCheckError


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
        assigns: list[SalesChannelViewAssign] | None = None,
    ) -> None:
        self.get_value_only = get_value_only
        self.value: Optional[Dict[str, Any]] = None
        self.price_payload: List[Dict[str, Any]] = []
        self.assigns = assigns
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

    def _get_assign_currency_map(self) -> dict[str, str]:
        currency_map: dict[str, str] = {}
        assigns = self.assigns
        if not assigns:
            assigns = list(
                SalesChannelViewAssign.objects.filter(
                    sales_channel=self.sales_channel,
                    product=self.local_instance,
                ).select_related("sales_channel_view")
            )

        global_currency_code: Optional[str] = None
        global_codes = (
            SheinRemoteCurrency.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view__isnull=True,
            )
            .exclude(remote_code__in=(None, ""))
            .values_list("remote_code", flat=True)
            .distinct()
        )
        if global_codes.count() == 1:
            global_currency_code = str(global_codes.first()).strip()  # type: ignore[arg-type]

        resolved_views: list[Any] = []
        resolved_view_ids: list[int] = []
        for assign in assigns:
            view = getattr(assign, "sales_channel_view", None)
            resolved_view = view.get_real_instance() if hasattr(view, "get_real_instance") else view
            if resolved_view is None:
                continue
            resolved_views.append(resolved_view)
            if getattr(resolved_view, "id", None):
                resolved_view_ids.append(resolved_view.id)

        currency_by_view_id: dict[int, str] = {}
        if resolved_view_ids:
            rows = (
                SheinRemoteCurrency.objects.filter(
                    sales_channel=self.sales_channel,
                    sales_channel_view_id__in=resolved_view_ids,
                )
                .exclude(remote_code__in=(None, ""))
                .values_list("sales_channel_view_id", "remote_code")
            )
            currency_by_view_id = {view_id: str(code).strip() for view_id, code in rows if view_id and code}

        for assign in assigns:
            site_code = getattr(assign.sales_channel_view, "remote_id", None)
            if not site_code:
                continue
            view = getattr(assign, "sales_channel_view", None)
            resolved_view = view.get_real_instance() if hasattr(view, "get_real_instance") else view
            currency = currency_by_view_id.get(getattr(resolved_view, "id", None))
            if not currency:
                raw_data = getattr(resolved_view, "raw_data", {}) if resolved_view is not None else {}
                currency = raw_data.get("currency") if isinstance(raw_data, dict) else None
            if not currency and global_currency_code:
                currency = global_currency_code
            if currency:
                currency_map[str(site_code).strip()] = str(currency).strip()

        return {k: v for k, v in currency_map.items() if k and v}

    def _build_price_info_list(self) -> List[Dict[str, Any]]:
        if not self.to_update_currencies:
            return []

        price_info_list: List[Dict[str, Any]] = []

        currency_map = self._get_assign_currency_map()
        if self.assigns and not currency_map:
            raise PreFlightCheckError(
                "Shein currency mapping is missing for assigned sub-sites. Pull Shein site list metadata first."
            )
        allowed_codes = {value for value in currency_map.values() if value}
        allowed_codes = allowed_codes.intersection(self.to_update_currencies) if allowed_codes else set(self.to_update_currencies)

        for currency_code in sorted(allowed_codes):
            price_entry = self.price_data.get(currency_code or "", {})

            base_price = price_entry.get("price")
            special_price = price_entry.get("discount_price")

            if base_price is None and special_price is None:
                continue

            entry: Dict[str, Any] = {
                "currency": currency_code,
                "base_price": base_price,
            }
            if special_price is not None:
                entry["special_price"] = special_price

            price_info_list.append(entry)

        return price_info_list

    def _build_product_price_payload(self) -> List[Dict[str, Any]]:
        assigns = self.assigns
        if not assigns:
            assigns = list(
                SalesChannelViewAssign.objects.filter(
                    sales_channel=self.sales_channel,
                    product=self.local_instance,
                ).select_related("sales_channel_view")
            )

        product_code = getattr(self.remote_product, "remote_id", None) or self.remote_product.remote_sku
        payload: List[Dict[str, Any]] = []

        currency_map = self._get_assign_currency_map()

        for site_entry in assigns:
            site_code = getattr(site_entry.sales_channel_view, "remote_id", None)
            if not site_code:
                continue
            currency_code = currency_map.get(str(site_code).strip())
            if not currency_code:
                continue
            values = self.price_data.get(currency_code, {})
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
