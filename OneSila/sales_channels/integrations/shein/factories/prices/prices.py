from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sales_channels.factories.prices.prices import RemotePriceUpdateFactory
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.models.products import RemotePrice
from sales_channels.exceptions import PreFlightCheckError

logger = logging.getLogger(__name__)


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
        include_all_prices: bool = False,
        assigns: list[SalesChannelViewAssign] | None = None,
        use_remote_prices: bool = False,
    ) -> None:
        self.get_value_only = get_value_only
        self.include_all_prices = include_all_prices
        self.use_remote_prices = use_remote_prices
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

    def run(self):
        if self.get_value_only:
            self.set_to_update_currencies()
            if self.include_all_prices:
                self.to_update_currencies = list(self.price_data.keys())
            self.value = {"price_info_list": self._build_price_info_list()}
            return self.value
        return super().run()

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

    def _resolve_spu_name(self) -> str:
        remote_product = getattr(self, "remote_product", None)
        if remote_product is None:
            return ""

        for attr in ("spu_name", "remote_id"):
            value = getattr(remote_product, attr, None)
            if value:
                return str(value).strip()

        parent = getattr(remote_product, "remote_parent_product", None)
        if parent is not None:
            for attr in ("spu_name", "remote_id"):
                value = getattr(parent, attr, None)
                if value:
                    return str(value).strip()

        return ""

    def _normalize_price_value(self, value: Any, treat_zero_as_none: bool) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return None
        if treat_zero_as_none and normalized == 0:
            return None
        return normalized

    def _prices_match(self, existing: Mapping[str, Any], price: Any, discount: Any) -> bool:
        existing_price = self._normalize_price_value(value=existing.get("price"), treat_zero_as_none=False)
        existing_discount = self._normalize_price_value(value=existing.get("discount_price"), treat_zero_as_none=True)
        desired_price = self._normalize_price_value(value=price, treat_zero_as_none=False)
        desired_discount = self._normalize_price_value(value=discount, treat_zero_as_none=True)
        return existing_price == desired_price and existing_discount == desired_discount

    def _extract_remote_price_data(
        self,
        *,
        spu_payload: Mapping[str, Any],
        sku_code: str,
    ) -> dict[str, dict[str, Any]]:
        skc_list = spu_payload.get("skcInfoList") or spu_payload.get("skc_info_list") or []
        if not isinstance(skc_list, Iterable):
            return {}

        for skc in skc_list:
            if not isinstance(skc, Mapping):
                continue
            sku_list = skc.get("skuInfoList") or skc.get("sku_info_list") or []
            if not isinstance(sku_list, Iterable):
                continue
            for sku in sku_list:
                if not isinstance(sku, Mapping):
                    continue
                remote_sku_code = str(sku.get("skuCode") or sku.get("sku_code") or "").strip()
                if not remote_sku_code or remote_sku_code != sku_code:
                    continue
                raw_prices = sku.get("priceInfoList") or sku.get("price_info_list") or []
                if not isinstance(raw_prices, Iterable):
                    return {}
                price_data: dict[str, dict[str, Any]] = {}
                for entry in raw_prices:
                    if not isinstance(entry, Mapping):
                        continue
                    currency_code = str(entry.get("currency") or "").strip()
                    if not currency_code:
                        continue
                    base_price = self._normalize_price_value(
                        value=entry.get("basePrice") or entry.get("base_price"),
                        treat_zero_as_none=False,
                    )
                    special_price = self._normalize_price_value(
                        value=entry.get("specialPrice") or entry.get("special_price"),
                        treat_zero_as_none=False,
                    )
                    if base_price is None and special_price is None:
                        continue
                    price_data[currency_code] = {
                        "price": base_price,
                        "discount_price": special_price,
                    }
                return price_data

        return {}

    def _fetch_remote_price_data(self) -> dict[str, dict[str, Any]]:
        if not self.use_remote_prices or self.get_value_only:
            return {}

        sku_code = str(getattr(self.remote_product, "sku_code", "") or "").strip()
        if not sku_code:
            return {}

        spu_name = self._resolve_spu_name()
        if not spu_name:
            return {}

        try:
            info = self.get_product(spu_name=spu_name)
        except Exception as exc:
            logger.warning("Shein price check failed for spu %s: %s", spu_name, exc)
            return {}

        if not isinstance(info, Mapping):
            return {}

        return self._extract_remote_price_data(spu_payload=info, sku_code=sku_code)

    def set_to_update_currencies(self):  # type: ignore[override]
        from sales_channels.models import RemoteCurrency
        from currencies.models import Currency

        if self.currency:
            reset_currency = Currency.objects.filter(
                inherits_from=self.currency,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
            ).exists()

            if reset_currency:
                self.currency = None

        try:
            stored_price_data = self.remote_instance.price_data or {}
        except AttributeError:
            stored_price_data = {}

        remote_price_data = self._fetch_remote_price_data()

        all_remote_currencies = RemoteCurrency.objects.filter(sales_channel=self.sales_channel)

        self.to_update_currencies = []
        self.price_data = {}

        for remote_currency in all_remote_currencies:
            local_currency = remote_currency.local_instance

            if not local_currency:
                continue

            limit_iso = getattr(self, "limit_to_currency_iso", None)
            if limit_iso and local_currency.iso_code != limit_iso:
                continue

            local_product = self.get_local_product()
            full_price, discount_price = local_product.get_price_for_sales_channel(
                self.sales_channel,
                currency=local_currency,
            )

            price = float(full_price) if full_price is not None else None
            discount = float(discount_price) if discount_price is not None else None

            self.price_data[local_currency.iso_code] = {
                "price": price,
                "discount_price": discount,
            }

            if not self.currency or self.currency == local_currency:
                currency_code = local_currency.iso_code
                stored_entry = stored_price_data.get(currency_code, {}) if isinstance(stored_price_data, dict) else {}
                if self._prices_match(existing=stored_entry, price=price, discount=discount):
                    continue

                if currency_code in remote_price_data:
                    remote_entry = remote_price_data.get(currency_code, {})
                    if self._prices_match(existing=remote_entry, price=price, discount=discount):
                        continue
                    self.to_update_currencies.append(currency_code)
                    continue

                if not self._prices_match(existing=stored_entry, price=price, discount=discount):
                    self.to_update_currencies.append(currency_code)

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

        product_code = getattr(self.remote_product, "sku_code", None)
        if not product_code:
            raise PreFlightCheckError(
                "Shein price updates require sku_code on the remote product. "
                "Sync the product to fetch sku_code before updating prices."
            )
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
        if self.get_value_only:
            self.value = {"price_info_list": self._build_price_info_list()}
            return self.value

        price_info_list = self._build_price_info_list()
        self.price_payload = self._build_product_price_payload()

        if not self.price_payload:
            return {}

        response = self.shein_post(
            path="/open-api/openapi-business-backend/product/price/save",
            payload={"productPriceList": self.price_payload},
        )
        return response.json() if hasattr(response, "json") else {}

    def serialize_response(self, response):
        return response or {}
