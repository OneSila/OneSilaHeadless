from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.utils.text import slugify

from products.models import Product
from properties.models import Property
from sales_channels.integrations.mirakl.models import (
    MiraklProductType,
    MiraklProperty,
    MiraklPropertySelectValue,
)


class MiraklReverseProductMapper:
    RESERVED_FIELD_CODES = {
        "offer-id",
        "offer_id",
        "product-sku",
        "product_sku",
        "shop-id",
        "shop_id",
        "shop-sku",
        "shop_sku",
        "active",
        "deleted",
        "channels",
        "price",
        "prices",
        "discount-price",
        "discount_price",
        "origin-price",
        "origin_price",
        "currency-iso-code",
        "currency_iso_code",
        "quantity",
        "product_title",
        "product_description",
        "allow_quote_requests",
        "available_end_date",
        "available_start_date",
        "date_created",
        "favorite_rank",
        "fulfillment",
        "is_professional",
        "last_updated",
        "leadtime_to_ship",
        "logistic_class",
        "max_order_quantity",
        "measurement",
        "min_order_quantity",
        "min_shipping_price",
        "min_shipping_price_additional",
        "min_shipping_type",
        "min_shipping_zone",
        "model",
        "msrp",
        "offer_additional_fields",
        "package_quantity",
        "price_additional_info",
        "product_tax_code",
        "retail_prices",
        "shipping_types",
        "shop_name",
        "state_code",
        "warehouses",
    }

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel
        self.company = sales_channel.multi_tenant_company
        self.default_language = getattr(self.company, "language", "en")
        self._property_by_code = {
            item.code: item
            for item in MiraklProperty.objects.filter(sales_channel=sales_channel).select_related("local_instance")
        }
        self._select_value_lookup = self._build_select_value_lookup()
        self._brand_property = self._resolve_brand_property()
        self._brand_value_lookup = self._build_brand_value_lookup()

    def build(self, *, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], object | None]:
        product_data = dict(payload.get("product") or {})
        export_rows = [row for row in payload.get("export_rows") or [] if isinstance(row, dict)]
        matched_offers = [row for row in payload.get("matched_offers") or [] if isinstance(row, dict)]
        merged_fields = self._merge_fields(
            product_data=product_data,
            export_rows=export_rows,
            matched_offers=matched_offers,
        )

        sku = self._first_non_empty(
            product_data.get("product_sku"),
            merged_fields.get("product_sku"),
            merged_fields.get("product-sku"),
            merged_fields.get("shop_sku"),
            merged_fields.get("shop-sku"),
        )
        if not sku:
            raise ValueError("Mirakl payload is missing product SKU.")

        title = self._first_non_empty(
            product_data.get("product_title"),
            merged_fields.get("product_title"),
            merged_fields.get("description"),
            sku,
        )
        description = self._first_non_empty(
            product_data.get("product_description"),
            merged_fields.get("description"),
            "",
        )
        subtitle = self._first_non_empty(
            product_data.get("product_subtitle"),
            merged_fields.get("product_subtitle"),
            "",
        )
        short_description = self._first_non_empty(
            product_data.get("product_short_description"),
            merged_fields.get("product_short_description"),
            description,
        )
        bullet_points = self._collect_bullet_points(merged_fields=merged_fields)
        references = [item for item in product_data.get("product_references") or [] if isinstance(item, dict)]
        ean_code = self._extract_ean_code(references=references)
        configurable_parent_sku = self._resolve_configurable_parent_sku(
            merged_fields=merged_fields,
            sku=sku,
        )
        price_entries, sales_pricelist_items = self._build_price_entries(
            export_rows=export_rows,
            matched_offers=matched_offers,
        )
        images, documents = self._build_media_entries(product_data=product_data)
        active = self._resolve_active(export_rows=export_rows)

        structured: dict[str, Any] = {
            "sku": sku,
            "name": title,
            "type": Product.SIMPLE,
            "active": active,
            "__mirakl_export_rows": export_rows,
            "translations": [
                {
                    "language": self.default_language,
                    "sales_channel": self.sales_channel,
                    "name": title,
                    "subtitle": subtitle,
                    "description": description,
                    "short_description": short_description,
                    "url_key": slugify(title) or slugify(sku),
                    "bullet_points": bullet_points,
                }
            ],
        }
        if ean_code:
            structured["ean_code"] = ean_code
        if configurable_parent_sku:
            structured["configurable_parent_sku"] = configurable_parent_sku
        if price_entries:
            structured["prices"] = price_entries
        if sales_pricelist_items:
            structured["sales_pricelist_items"] = sales_pricelist_items
        if images:
            structured["images"] = images
        if documents:
            structured["documents"] = documents

        brand_property_entry = self._build_brand_property_entry(merged_fields=merged_fields)
        properties = []
        if brand_property_entry is not None:
            properties.append(brand_property_entry)
        properties.extend(self._build_property_entries(merged_fields=merged_fields))
        properties.extend(
            self._build_offer_metadata_properties(
                merged_fields=merged_fields,
                skip_codes={"product_brand"} if brand_property_entry is not None else None,
            )
        )
        if properties:
            structured["properties"] = properties

        product_rule = self._resolve_product_rule(product_data=product_data)
        structured_log = {
            "remote_payload": {
                "product": product_data,
                "export_rows": export_rows,
                "matched_offers": matched_offers,
                "merged_fields": merged_fields,
            },
            "resolved_payload": structured,
        }
        return structured, structured_log, product_rule

    def _merge_fields(
        self,
        *,
        product_data: dict[str, Any],
        export_rows: list[dict[str, Any]],
        matched_offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        if product_data:
            merged.update(product_data)
        for row in export_rows:
            for key, value in row.items():
                if key not in merged or merged.get(key) in (None, "", [], {}):
                    merged[key] = value
        for offer in matched_offers:
            for key, value in offer.items():
                if key not in merged or merged.get(key) in (None, "", [], {}):
                    merged[key] = value
        return merged

    def _build_property_entries(self, *, merged_fields: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for code, raw_value in merged_fields.items():
            if code in self.RESERVED_FIELD_CODES:
                continue
            if raw_value in (None, "", [], {}):
                continue

            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                property_type = self._infer_property_type(raw_value=raw_value)
                results.append(
                    {
                        "property_data": {
                            "internal_name": code,
                            "name": code.replace("_", " ").replace("-", " ").title(),
                            "type": property_type,
                            "is_public_information": True,
                            "add_to_filters": False,
                        },
                        "value": self._normalize_property_value(raw_value=raw_value, property_type=property_type),
                    }
                )
                continue

            property_type = remote_property.local_instance.type if remote_property.local_instance_id else remote_property.type or self._infer_property_type(raw_value=raw_value)
            normalized_value = self._normalize_property_value(raw_value=raw_value, property_type=property_type)
            entry: dict[str, Any] = {"value": normalized_value}
            if remote_property.local_instance_id:
                entry["property"] = remote_property.local_instance
            else:
                entry["property_data"] = {
                    "internal_name": remote_property.code,
                    "name": remote_property.name or remote_property.code.replace("_", " ").replace("-", " ").title(),
                    "type": property_type,
                    "is_public_information": True,
                    "add_to_filters": False,
                }
            if property_type in {Property.TYPES.SELECT, Property.TYPES.MULTISELECT}:
                mapped_value, value_is_id = self._map_select_value(
                    remote_property=remote_property,
                    normalized_value=normalized_value,
                    property_type=property_type,
                )
                entry["value"] = mapped_value
                if value_is_id:
                    entry["value_is_id"] = True
            results.append(entry)
        return results

    def _build_select_value_lookup(self) -> dict[tuple[int, str], MiraklPropertySelectValue]:
        lookup: dict[tuple[int, str], MiraklPropertySelectValue] = {}
        queryset = MiraklPropertySelectValue.objects.filter(
            sales_channel=self.sales_channel,
        ).select_related("local_instance", "remote_property")
        for item in queryset:
            for candidate in {item.code, item.value}:
                normalized = str(candidate or "").strip().lower()
                if normalized:
                    lookup[(item.remote_property_id, normalized)] = item
        return lookup

    def _resolve_brand_property(self) -> Property | None:
        return Property.objects.filter(
            multi_tenant_company=self.company,
            internal_name="brand",
        ).first()

    def _build_brand_value_lookup(self) -> dict[str, MiraklPropertySelectValue]:
        if self._brand_property is None:
            return {}

        lookup: dict[str, MiraklPropertySelectValue] = {}
        queryset = (
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property__local_instance=self._brand_property,
                local_instance__isnull=False,
            )
            .select_related("local_instance")
            .order_by("id")
        )
        for item in queryset:
            normalized = str(item.value or "").strip().lower()
            if normalized and normalized not in lookup:
                lookup[normalized] = item
        return lookup

    def _build_brand_property_entry(self, *, merged_fields: dict[str, Any]) -> dict[str, Any] | None:
        if self._brand_property is None:
            return None

        brand_value = str(merged_fields.get("product_brand") or "").strip()
        if not brand_value:
            return None

        mapped_value = self._brand_value_lookup.get(brand_value.lower())
        if mapped_value is None or not mapped_value.local_instance_id:
            return None

        return {
            "property": self._brand_property,
            "value": mapped_value.local_instance_id,
            "value_is_id": True,
        }

    def _map_select_value(
        self,
        *,
        remote_property: MiraklProperty,
        normalized_value: Any,
        property_type: str,
    ) -> tuple[Any, bool]:
        if property_type == Property.TYPES.SELECT:
            lookup_key = (remote_property.id, str(normalized_value or "").strip().lower())
            mapped = self._select_value_lookup.get(lookup_key)
            if mapped is not None and mapped.local_instance_id:
                return mapped.local_instance_id, True
            return normalized_value, False

        mapped_ids: list[int] = []
        fallback_values: list[str] = []
        values = normalized_value if isinstance(normalized_value, list) else [normalized_value]
        for value in values:
            lookup_key = (remote_property.id, str(value or "").strip().lower())
            mapped = self._select_value_lookup.get(lookup_key)
            if mapped is not None and mapped.local_instance_id:
                mapped_ids.append(mapped.local_instance_id)
            elif value not in (None, ""):
                fallback_values.append(str(value))
        if mapped_ids and not fallback_values:
            return mapped_ids, True
        return fallback_values or normalized_value, False

    def _infer_property_type(self, *, raw_value: Any) -> str:
        if isinstance(raw_value, bool):
            return Property.TYPES.BOOLEAN
        if isinstance(raw_value, int) and not isinstance(raw_value, bool):
            return Property.TYPES.INT
        if isinstance(raw_value, float):
            return Property.TYPES.FLOAT
        if isinstance(raw_value, list):
            return Property.TYPES.MULTISELECT
        return Property.TYPES.TEXT

    def _normalize_property_value(self, *, raw_value: Any, property_type: str) -> Any:
        if property_type == Property.TYPES.MULTISELECT:
            if isinstance(raw_value, list):
                return [str(item).strip() for item in raw_value if str(item).strip()]
            separator = getattr(self.sales_channel, "list_of_multiple_values_separator", None) or ","
            return [part.strip() for part in str(raw_value).split(separator) if part.strip()]
        if property_type == Property.TYPES.BOOLEAN:
            if isinstance(raw_value, str):
                return raw_value.strip().lower() in {"true", "1", "yes", "y"}
            return bool(raw_value)
        return raw_value

    def _collect_bullet_points(self, *, merged_fields: dict[str, Any]) -> list[str]:
        buckets: dict[int, str] = {}
        for code, value in merged_fields.items():
            if not value:
                continue
            remote_property = self._property_by_code.get(code)
            if remote_property and remote_property.representation_type == MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT:
                index = self._extract_suffix(value=code)
                buckets[index] = str(value).strip()
                continue
            normalized = str(code).lower()
            if "bullet" in normalized:
                index = self._extract_suffix(value=code)
                buckets[index] = str(value).strip()
        return [value for _index, value in sorted(buckets.items()) if value]

    def _extract_ean_code(self, *, references: list[dict[str, Any]]) -> str:
        for item in references:
            if str(item.get("reference_type") or "").upper() == "EAN":
                value = str(item.get("reference") or "").strip()
                if value:
                    return value
        return ""

    def _build_price_entries(
        self,
        *,
        export_rows: list[dict[str, Any]],
        matched_offers: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        prices: list[dict[str, Any]] = []
        sales_pricelist_items: list[dict[str, Any]] = []
        seen_currencies: set[str] = set()
        pricing_rows = matched_offers or export_rows
        if not pricing_rows:
            pricing_rows = export_rows
        for row in pricing_rows:
            currency = str(row.get("currency-iso-code") or row.get("currency_iso_code") or "").strip()
            if not currency:
                prices_payload = row.get("prices") or row.get("retail_prices") or []
                if isinstance(prices_payload, list):
                    for price_row in prices_payload:
                        if not isinstance(price_row, dict):
                            continue
                        nested_currency = str(price_row.get("currency_iso_code") or price_row.get("currency") or "").strip()
                        if nested_currency:
                            currency = nested_currency
                            break
            if not currency or currency in seen_currencies:
                continue
            seen_currencies.add(currency)
            origin, current = self._extract_prices_from_row(row=row)
            if origin in (None, "") and current in (None, ""):
                continue
            if current in (None, ""):
                current = origin
            if origin in (None, ""):
                origin = current
            prices.append(
                {
                    "currency": currency,
                    "rrp": origin,
                    "price": current,
                }
            )
            sales_pricelist_items.append(
                {
                    "salespricelist_data": {
                        "name": f"Mirakl {self.sales_channel.hostname} {currency}",
                        "currency": currency,
                    },
                    "price_auto": origin if origin not in (None, "") else current,
                    "discount_auto": current if origin not in (None, "") and current not in (None, "") else None,
                    "disable_auto_update": True,
                }
            )
        return prices, sales_pricelist_items

    def _extract_prices_from_row(self, *, row: dict[str, Any]) -> tuple[Any, Any]:
        origin = row.get("origin-price")
        if origin in (None, ""):
            origin = row.get("origin_price")
        current = row.get("discount-price")
        if current in (None, ""):
            current = row.get("discount_price")
        if current in (None, ""):
            current = row.get("price")

        applicable_pricing = row.get("applicable_pricing") or {}
        if isinstance(applicable_pricing, dict):
            if origin in (None, ""):
                origin = applicable_pricing.get("unit_origin_price")
            if current in (None, ""):
                current = applicable_pricing.get("unit_discount_price")
            if current in (None, ""):
                current = applicable_pricing.get("price")

        if origin in (None, "") and current in (None, ""):
            price_entry = self._extract_price_entry(row=row)
            if price_entry is not None:
                origin = (
                    price_entry.get("origin_price")
                    or price_entry.get("unit_origin_price")
                )
                current = price_entry.get("unit_discount_price")
                if current in (None, ""):
                    current = price_entry.get("discount_price")
                if current in (None, ""):
                    current = price_entry.get("price")
                if current in (None, ""):
                    volume_prices = price_entry.get("volume_prices") or []
                    if volume_prices and isinstance(volume_prices[0], dict):
                        current = volume_prices[0].get("price")
                        if origin in (None, ""):
                            origin = volume_prices[0].get("unit_origin_price")

        return origin, current

    def _build_offer_metadata_properties(
        self,
        *,
        merged_fields: dict[str, Any],
        skip_codes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        property_codes = [
            "allow_quote_requests",
            "channels",
            "currency_iso_code",
            "date_created",
            "deleted",
            "is_professional",
            "last_updated",
            "leadtime_to_ship",
            "max_order_quantity",
            "min_order_quantity",
            "min_shipping_price",
            "min_shipping_price_additional",
            "min_shipping_type",
            "min_shipping_zone",
            "model",
            "msrp",
            "offer_id",
            "package_quantity",
            "premium",
            "price_additional_info",
            "product_brand",
            "product_tax_code",
            "quantity",
            "shop_id",
            "shop_name",
            "shop_sku",
            "shipping_deadline",
            "state_code",
            "total_price",
        ]
        results: list[dict[str, Any]] = []
        for code in property_codes:
            if skip_codes and code in skip_codes:
                continue
            raw_value = merged_fields.get(code)
            if raw_value in (None, "", [], {}):
                continue
            property_type = self._infer_property_type(raw_value=raw_value)
            results.append(
                {
                    "property_data": {
                        "internal_name": code,
                        "name": code.replace("_", " ").title(),
                        "type": property_type,
                        "is_public_information": True,
                        "add_to_filters": False,
                    },
                    "value": self._normalize_property_value(
                        raw_value=raw_value,
                        property_type=property_type,
                    ),
                }
            )

        fulfillment = merged_fields.get("fulfillment") or {}
        if isinstance(fulfillment, dict):
            center = fulfillment.get("center") or {}
            if isinstance(center, dict):
                center_code = str(center.get("code") or "").strip()
                if center_code:
                    results.append(
                        {
                            "property_data": {
                                "internal_name": "fulfillment_center_code",
                                "name": "Fulfillment Center Code",
                                "type": Property.TYPES.TEXT,
                                "is_public_information": True,
                                "add_to_filters": False,
                            },
                            "value": center_code,
                        }
                    )

        logistic_class = merged_fields.get("logistic_class") or {}
        if isinstance(logistic_class, dict):
            logistic_class_code = str(logistic_class.get("code") or "").strip()
            if logistic_class_code:
                results.append(
                    {
                        "property_data": {
                            "internal_name": "logistic_class_code",
                            "name": "Logistic Class Code",
                            "type": Property.TYPES.TEXT,
                            "is_public_information": True,
                            "add_to_filters": False,
                        },
                        "value": logistic_class_code,
                    }
                )

        return results

    def _build_media_entries(self, *, product_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        images: list[dict[str, Any]] = []
        documents: list[dict[str, Any]] = []
        product_media = product_data.get("product_media") or []
        if isinstance(product_media, dict):
            product_media = [product_media]
        for index, media in enumerate(product_media):
            if not isinstance(media, dict):
                continue
            url = str(media.get("dam_url") or media.get("media_url") or "").strip()
            if not url:
                continue
            media_type = str(media.get("type") or "").lower()
            if "image" in media_type or media_type in {"small", "large", "thumbnail"}:
                images.append(
                    {
                        "image_url": url,
                        "sort_order": index,
                        "is_main_image": index == 0,
                    }
                )
            else:
                documents.append({"document_url": url})
        return images, documents

    def _resolve_active(self, *, export_rows: list[dict[str, Any]]) -> bool:
        if not export_rows:
            return True
        for row in export_rows:
            deleted = row.get("deleted")
            active = row.get("active")
            if deleted in (True, "true", "TRUE", 1, "1"):
                continue
            if active in (True, "true", "TRUE", 1, "1", None, ""):
                return True
        return False

    def _resolve_product_rule(self, *, product_data: dict[str, Any]):
        category_code = str(product_data.get("category_code") or "").strip()
        if not category_code:
            return None
        product_type = (
            MiraklProductType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id=category_code,
                local_instance__isnull=False,
            )
            .select_related("local_instance")
            .first()
        )
        return getattr(product_type, "local_instance", None)

    def _resolve_configurable_parent_sku(self, *, merged_fields: dict[str, Any], sku: str) -> str:
        for code, value in merged_fields.items():
            if value in (None, ""):
                continue
            remote_property = self._property_by_code.get(code)
            if remote_property is not None and remote_property.representation_type == MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU:
                candidate = str(value).strip()
                if candidate and candidate != sku:
                    return candidate

        for code in ("configurable_sku", "parent_sku", "parent-product-sku", "parent_product_sku"):
            candidate = str(merged_fields.get(code) or "").strip()
            if candidate and candidate != sku:
                return candidate
        return ""

    def _extract_price_entry(self, *, row: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("prices", "retail_prices"):
            price_rows = row.get(key) or []
            if not isinstance(price_rows, list):
                continue
            for price_row in price_rows:
                if not isinstance(price_row, dict):
                    continue
                if price_row.get("price") in (None, "") and price_row.get("unit_origin_price") in (None, ""):
                    continue
                return price_row
        return None

    def _extract_suffix(self, *, value: str) -> int:
        digits = "".join(character for character in str(value or "") if character.isdigit())
        return int(digits) if digits else 0

    def _first_non_empty(self, *values: Any) -> str:
        for value in values:
            if value in (None, ""):
                continue
            return str(value).strip()
        return ""
