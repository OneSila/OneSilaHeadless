"""Value parsing helpers for Shein product imports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from currencies.models import Currency
from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.models import SheinRemoteLanguage
from sales_channels.models import SalesChannelIntegrationPricelist
from sales_prices.models import SalesPrice

from .product_utils import coerce_decimal, normalize_text


class SheinProductImportValueParser:
    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self._remote_language_cache: dict[str, str | None] = {}

    def resolve_language_code(self, *, remote_code: str | None) -> str | None:
        if not remote_code:
            return None
        normalized = remote_code.strip().lower()
        if not normalized:
            return None
        cached = self._remote_language_cache.get(normalized)
        if cached is not None:
            return cached
        remote_language = (
            SheinRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                remote_code__iexact=normalized,
            )
            .exclude(local_instance__isnull=True)
            .exclude(local_instance="")
            .first()
        )
        local_code = remote_language.local_instance if remote_language else None
        if not local_code:
            local_code = normalized if normalized in constants.SHEIN_LANGUAGE_HEADER_MAP.values() else None
        self._remote_language_cache[normalized] = local_code
        return local_code

    def parse_translations(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        name_list = spu_payload.get("productMultiNameList") or spu_payload.get("product_multi_name_list") or []
        if skc_payload:
            override = skc_payload.get("productMultiNameList") or skc_payload.get("product_multi_name_list")
            if isinstance(override, list) and override:
                name_list = override
        desc_list = spu_payload.get("productMultiDescList") or spu_payload.get("product_multi_desc_list") or []

        name_by_language: dict[str, str] = {}
        desc_by_language: dict[str, str] = {}

        for entry in name_list:
            if not isinstance(entry, Mapping):
                continue
            language = self.resolve_language_code(remote_code=normalize_text(value=entry.get("language")))
            name = normalize_text(value=entry.get("productName") or entry.get("product_name"))
            if language and name and language not in name_by_language:
                name_by_language[language] = name

        for entry in desc_list:
            if not isinstance(entry, Mapping):
                continue
            language = self.resolve_language_code(remote_code=normalize_text(value=entry.get("language")))
            desc = normalize_text(value=entry.get("productDesc") or entry.get("product_desc"))
            if language and desc and language not in desc_by_language:
                desc_by_language[language] = desc

        translations: list[dict[str, Any]] = []
        default_language = None

        for language, name in name_by_language.items():
            translation: dict[str, Any] = {"name": name, "language": language}
            description = desc_by_language.get(language)
            if description is not None:
                translation["description"] = description
            translations.append(translation)
            if default_language is None:
                default_language = language

        if default_language is None:
            default_language = self.multi_tenant_company.language or None

        return translations, default_language

    def parse_images(
        self,
        *,
        skc_payload: Mapping[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        if not isinstance(skc_payload, Mapping):
            return [], {}

        images: list[dict[str, Any]] = []
        remote_id_map: dict[str, str] = {}
        seen_urls: set[str] = set()

        def append_entry(*, url: str | None, remote_id: Any | None, is_main: bool) -> None:
            if not url or url in seen_urls:
                return
            sort_order = len(images)
            images.append(
                {
                    "image_url": url,
                    "sort_order": sort_order,
                    "is_main_image": is_main,
                }
            )
            if remote_id is not None:
                remote_id_map[str(sort_order)] = str(remote_id)
            seen_urls.add(url)

        raw_skc_images = skc_payload.get("skcImageInfoList") or skc_payload.get("skc_image_info_list") or []
        if isinstance(raw_skc_images, Iterable):
            sorted_images = sorted(
                [entry for entry in raw_skc_images if isinstance(entry, Mapping)],
                key=lambda entry: entry.get("sort") or entry.get("imageSort") or 0,
            )
            for entry in sorted_images:
                url = normalize_text(value=entry.get("imageUrl") or entry.get("image_url"))
                image_type = normalize_text(value=entry.get("imageType") or entry.get("image_type")) or ""
                is_main = image_type.upper() == "MAIN" or not images
                append_entry(
                    url=url,
                    remote_id=entry.get("imageItemId") or entry.get("image_item_id"),
                    is_main=is_main,
                )

        site_detail_list = skc_payload.get("siteDetailImageInfoList") or skc_payload.get("site_detail_image_info_list") or []
        if isinstance(site_detail_list, Iterable):
            for group in site_detail_list:
                if not isinstance(group, Mapping):
                    continue
                info_list = group.get("imageInfoList") or group.get("image_info_list") or []
                for entry in info_list:
                    if not isinstance(entry, Mapping):
                        continue
                    url = normalize_text(value=entry.get("imageUrl") or entry.get("image_url"))
                    append_entry(
                        url=url,
                        remote_id=entry.get("imageItemId") or entry.get("image_item_id"),
                        is_main=False,
                    )

        return images, remote_id_map

    def parse_prices(
        self,
        *,
        sku_payload: Mapping[str, Any] | None,
        local_product: Any | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not isinstance(sku_payload, Mapping):
            return [], []

        raw_prices = sku_payload.get("priceInfoList") or sku_payload.get("price_info_list") or []
        if not isinstance(raw_prices, Iterable):
            return [], []

        price_by_currency: dict[str, dict[str, Any]] = {}

        for entry in raw_prices:
            if not isinstance(entry, Mapping):
                continue
            currency_code = normalize_text(value=entry.get("currency"))
            if not currency_code:
                continue
            base_price = coerce_decimal(value=entry.get("basePrice") or entry.get("base_price"))
            special_price = coerce_decimal(value=entry.get("specialPrice") or entry.get("special_price"))
            if base_price is None and special_price is None:
                continue
            actual_price = special_price if special_price not in (None, 0) else base_price
            if actual_price is None:
                continue
            if currency_code not in price_by_currency:
                price_by_currency[currency_code] = {
                    "price": actual_price,
                    "rrp": base_price if special_price not in (None, 0) else None,
                }

        prices: list[dict[str, Any]] = []
        sales_pricelist_items: list[dict[str, Any]] = []

        for currency_code, values in price_by_currency.items():
            iso_code = str(currency_code).upper()
            try:
                currency = Currency.objects.get(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    iso_code=iso_code,
                )
            except Currency.DoesNotExist as exc:
                raise ValueError(
                    f"Currency with ISO code {iso_code} does not exist locally"
                ) from exc

            scip = (
                SalesChannelIntegrationPricelist.objects.filter(
                    sales_channel=self.sales_channel,
                    price_list__currency=currency,
                )
                .select_related("price_list")
                .first()
            )

            price_decimal = values.get("price")
            if price_decimal is None:
                continue

            if scip:
                sales_pricelist_items.append(
                    {
                        "salespricelist": scip.price_list,
                        "disable_auto_update": True,
                        "price_auto": price_decimal,
                    }
                )
            else:
                sales_pricelist_items.append(
                    {
                        "salespricelist_data": {
                            "name": f"Shein {self.sales_channel.hostname} {iso_code}",
                            "currency_object": currency,
                        },
                        "disable_auto_update": True,
                        "price_auto": price_decimal,
                    }
                )

            has_sales_price = (
                local_product
                and SalesPrice.objects.filter(
                    product=local_product,
                    currency__iso_code=iso_code,
                ).exists()
            )

            if not has_sales_price:
                price_payload: dict[str, Any] = {
                    "price": price_decimal,
                    "currency": iso_code,
                }
                rrp = values.get("rrp")
                if rrp is not None:
                    price_payload["rrp"] = rrp
                prices.append(price_payload)

        return prices, sales_pricelist_items
