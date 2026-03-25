from __future__ import annotations

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
        "active",
        "all_prices",
        "allow_quote_requests",
        "applicable_pricing",
        "available_end_date",
        "available_start_date",
        "category_code",
        "category_label",
        "channels",
        "currency_iso_code",
        "date_created",
        "deleted",
        "description",
        "discount",
        "favorite_rank",
        "fulfillment",
        "inactivity_reasons",
        "internal_description",
        "is_professional",
        "last_updated",
        "leadtime_to_ship",
        "logistic_class",
        "max_order_quantity",
        "min_order_quantity",
        "min_shipping_price",
        "min_shipping_price_additional",
        "min_shipping_type",
        "min_shipping_zone",
        "msrp",
        "offer_additional_fields",
        "offer_id",
        "offers",
        "package_quantity",
        "price",
        "price_additional_info",
        "product_brand",
        "product_description",
        "product_id",
        "product_id_type",
        "product_media",
        "product_medias",
        "product_references",
        "product_sku",
        "product_tax_code",
        "product_title",
        "quantity",
        "retail_prices",
        "shipping_deadline",
        "shop_id",
        "shop_name",
        "shop_sku",
        "state_code",
        "total_price",
        "total_count",
        "warehouses",
        "measurement",
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
        offer = dict(payload.get("offer") or {})
        p11_product = dict(payload.get("p11_product") or {})
        p31_product = dict(payload.get("p31_product") or {})
        merged_fields = self._merge_fields(
            offer=offer,
            p11_product=p11_product,
            p31_product=p31_product,
        )

        sku = self._first_non_empty(
            offer.get("shop_sku"),
            merged_fields.get("shop_sku"),
        )
        if not sku:
            raise ValueError("Mirakl OF21 payload is missing shop_sku.")

        remote_sku = self._first_non_empty(
            offer.get("product_sku"),
            merged_fields.get("product_sku"),
        )
        remote_id = self._first_non_empty(
            p31_product.get("product_id"),
            merged_fields.get("product_id"),
        )
        title = self._first_non_empty(
            offer.get("product_title"),
            merged_fields.get("product_title"),
            sku,
        )
        description = self._first_non_empty(
            offer.get("product_description"),
            merged_fields.get("product_description"),
            "",
        )
        short_description = self._first_non_empty(
            offer.get("internal_description"),
            merged_fields.get("internal_description"),
            "",
        )
        subtitle = self._first_non_empty(
            merged_fields.get("product_subtitle"),
            "",
        )
        bullet_points = self._collect_bullet_points(merged_fields=merged_fields)
        references = self._extract_references(
            offer=offer,
            p11_product=p11_product,
            p31_product=p31_product,
        )
        ean_code = self._extract_ean_code(references=references)
        price_entries, sales_pricelist_items = self._build_price_entries(offer=offer)
        images, documents = self._build_media_entries(product_data=p11_product or p31_product)
        active = self._resolve_active(offer=offer)

        structured: dict[str, Any] = {
            "sku": sku,
            "name": title,
            "type": Product.SIMPLE,
            "active": active,
            "__mirakl_offer_id": self._first_non_empty(offer.get("offer_id")),
            "__mirakl_remote_id": remote_id,
            "__mirakl_remote_sku": remote_sku,
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

        product_rule = self._resolve_product_rule(merged_fields=merged_fields)
        structured_log = {
            "remote_payload": {
                "offer": offer,
                "p11_product": p11_product,
                "p31_product": p31_product,
                "merged_fields": merged_fields,
            },
            "resolved_payload": {
                **structured,
                "__mirakl_remote_id": remote_id,
                "__mirakl_remote_sku": remote_sku,
            },
        }
        return structured, structured_log, product_rule

    def _merge_fields(
        self,
        *,
        offer: dict[str, Any],
        p11_product: dict[str, Any],
        p31_product: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(offer)
        for source in (p11_product, p31_product):
            for key, value in source.items():
                if key not in merged or merged.get(key) in (None, "", [], {}):
                    merged[key] = value
        return merged

    def _extract_references(
        self,
        *,
        offer: dict[str, Any],
        p11_product: dict[str, Any],
        p31_product: dict[str, Any],
    ) -> list[dict[str, Any]]:
        references = offer.get("product_references") or []
        if not isinstance(references, list) or not references:
            references = p11_product.get("product_references") or []
        if not isinstance(references, list) or not references:
            references = p31_product.get("product_references") or []
        if not isinstance(references, list):
            return []
        return [reference for reference in references if isinstance(reference, dict)]

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

            property_type = (
                remote_property.local_instance.type
                if remote_property.local_instance_id
                else remote_property.type or self._infer_property_type(raw_value=raw_value)
            )
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
        queryset = MiraklPropertySelectValue.objects.filter(sales_channel=self.sales_channel).select_related("local_instance", "remote_property")
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
                buckets[self._extract_suffix(value=code)] = str(value).strip()
                continue
            normalized = str(code).lower()
            if "bullet" in normalized:
                buckets[self._extract_suffix(value=code)] = str(value).strip()
        return [value for _index, value in sorted(buckets.items()) if value]

    def _extract_ean_code(self, *, references: list[dict[str, Any]]) -> str:
        for item in references:
            reference_type = str(item.get("reference_type") or "").upper()
            if reference_type == "EAN" or reference_type.startswith("EAN-"):
                value = str(item.get("reference") or "").strip()
                if value:
                    return value
        return ""

    def _build_price_entries(self, *, offer: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        currency = str(offer.get("currency_iso_code") or "").strip()
        if not currency:
            return [], []

        price = self._extract_offer_price(offer=offer)
        rrp = offer.get("msrp")
        if price in (None, "") and rrp in (None, ""):
            return [], []

        entry = {
            "currency": currency,
            "price": price,
        }
        if rrp not in (None, ""):
            entry["rrp"] = rrp

        sales_pricelist_item = {
            "salespricelist_data": {
                "name": f"Mirakl {self.sales_channel.hostname} {currency}",
                "currency": currency,
            },
            "price_auto": rrp if rrp not in (None, "") else price,
            "discount_auto": price if rrp not in (None, "") and price not in (None, "") else None,
            "disable_auto_update": True,
        }
        return [entry], [sales_pricelist_item]

    def _extract_offer_price(self, *, offer: dict[str, Any]) -> Any:
        direct_price = offer.get("price")
        if direct_price not in (None, ""):
            return direct_price

        applicable_pricing = offer.get("applicable_pricing") or {}
        if isinstance(applicable_pricing, dict):
            applicable_price = applicable_pricing.get("price")
            if applicable_price not in (None, ""):
                return applicable_price

        all_prices = offer.get("all_prices") or []
        if isinstance(all_prices, list):
            for price_row in all_prices:
                if not isinstance(price_row, dict):
                    continue
                price = price_row.get("price")
                if price not in (None, ""):
                    return price
        return None

    def _build_offer_metadata_properties(
        self,
        *,
        merged_fields: dict[str, Any],
        skip_codes: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        property_codes = [
            "allow_quote_requests",
            "category_code",
            "category_label",
            "channels",
            "currency_iso_code",
            "date_created",
            "internal_description",
            "is_professional",
            "last_updated",
            "leadtime_to_ship",
            "min_shipping_price",
            "min_shipping_price_additional",
            "min_shipping_type",
            "min_shipping_zone",
            "msrp",
            "offer_id",
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
                    "value": self._normalize_property_value(raw_value=raw_value, property_type=property_type),
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
        product_media = self._extract_product_media(product_data=product_data)
        for index, media in enumerate(product_media):
            if not isinstance(media, dict):
                continue
            url = str(media.get("dam_url") or media.get("media_url") or "").strip()
            if not url:
                continue
            media_type = str(media.get("type") or "").lower()
            if self._is_image_media(url=url, media_type=media_type):
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

    def _extract_product_media(self, *, product_data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("product_media", "product_medias", "media", "medias"):
            media_payload = product_data.get(key)
            normalized = self._normalize_media_payload(media_payload=media_payload)
            if normalized:
                return normalized
        return []

    def _normalize_media_payload(self, *, media_payload: Any) -> list[dict[str, Any]]:
        if isinstance(media_payload, list):
            return [item for item in media_payload if isinstance(item, dict)]

        if not isinstance(media_payload, dict):
            return []

        if media_payload.get("dam_url") or media_payload.get("media_url"):
            return [media_payload]

        for nested_key in ("items", "results", "product_media", "product_medias", "media", "medias"):
            nested_payload = media_payload.get(nested_key)
            normalized = self._normalize_media_payload(media_payload=nested_payload)
            if normalized:
                return normalized

        return []

    def _is_image_media(self, *, url: str, media_type: str) -> bool:
        if "image" in media_type or media_type in {"small", "large", "thumbnail"}:
            return True

        lowered_url = url.lower()
        if any(lowered_url.endswith(extension) for extension in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")):
            return True

        if any(lowered_url.endswith(extension) for extension in (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".zip")):
            return False

        return not media_type

    def _resolve_active(self, *, offer: dict[str, Any]) -> bool:
        deleted = offer.get("deleted")
        if deleted in (True, "true", "TRUE", 1, "1"):
            return False
        active = offer.get("active")
        return active in (True, "true", "TRUE", 1, "1", None, "")

    def _resolve_product_rule(self, *, merged_fields: dict[str, Any]):
        category_code = str(merged_fields.get("category_code") or "").strip()
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

    def _extract_suffix(self, *, value: str) -> int:
        digits = "".join(character for character in str(value or "") if character.isdigit())
        return int(digits) if digits else 0

    def _first_non_empty(self, *values: Any) -> str:
        for value in values:
            if value in (None, ""):
                continue
            return str(value).strip()
        return ""
