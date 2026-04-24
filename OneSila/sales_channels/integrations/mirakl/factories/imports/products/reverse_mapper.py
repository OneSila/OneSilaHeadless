from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils.text import slugify

from media.models import Image
from products.models import Product
from properties.models import Property
from sales_channels.exceptions import MiraklImportMissingProductSkuError
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklProductType,
    MiraklProperty,
    MiraklPropertySelectValue,
)


@dataclass(slots=True)
class MiraklMappedRow:
    shop_sku: str
    remote_sku: str
    category_code: str
    rule: Any | None
    is_configurable: bool
    parent_sku: str
    parent_payload: dict[str, Any] | None
    child_payload: dict[str, Any]
    view_codes: list[str]
    offer_data: dict[str, Any]


class MiraklReverseProductMapper:
    PROPERTY_REPRESENTATIONS = {
        MiraklProperty.REPRESENTATION_PROPERTY,
        MiraklProperty.REPRESENTATION_UNIT,
        MiraklProperty.REPRESENTATION_DEFAULT_VALUE,
        MiraklProperty.REPRESENTATION_CONDITION,
        MiraklProperty.REPRESENTATION_LOGISTIC_CLASS,
    }

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel
        self.company = sales_channel.multi_tenant_company
        self.default_language = getattr(self.company, "language", "en")
        self._property_by_code = {
            item.code: item
            for item in MiraklProperty.objects.filter(sales_channel=sales_channel).select_related("local_instance")
        }
        self._leaf_categories = list(
            MiraklCategory.objects.filter(
                sales_channel=sales_channel,
                is_leaf=True,
            )
        )
        self._leaf_category_by_remote_id = {
            str(item.remote_id or "").strip(): item
            for item in self._leaf_categories
            if str(item.remote_id or "").strip()
        }
        self._leaf_category_remote_id_by_name = {}
        for item in self._leaf_categories:
            normalized_name = self._normalize_lookup_token(value=item.name)
            if normalized_name and normalized_name not in self._leaf_category_remote_id_by_name:
                self._leaf_category_remote_id_by_name[normalized_name] = str(item.remote_id or "").strip()
        self._product_types = list(
            MiraklProductType.objects.filter(sales_channel=sales_channel).select_related("local_instance", "category")
        )
        self._product_type_by_remote_id = {
            str(item.remote_id or "").strip(): item
            for item in self._product_types
            if str(item.remote_id or "").strip()
        }
        self._product_type_by_name = {}
        for item in self._product_types:
            normalized_name = self._normalize_lookup_token(value=item.name)
            if normalized_name and normalized_name not in self._product_type_by_name:
                self._product_type_by_name[normalized_name] = item
        self._select_value_lookup: dict[tuple[int, str], MiraklPropertySelectValue] = {}
        self._loaded_select_value_property_ids: set[int] = set()
        self._document_type_by_remote_id = {
            str(item.remote_id or "").strip(): item
            for item in MiraklDocumentType.objects.filter(sales_channel=sales_channel)
            .select_related("local_instance")
            .order_by("id")
            if str(item.remote_id or "").strip()
        }

    def build(
        self,
        *,
        row_fields: dict[str, str],
        offer_data: dict[str, Any] | None = None,
    ) -> MiraklMappedRow:
        offer_data = dict(offer_data or {})
        self._ensure_select_value_lookup_for_headers(row_fields=row_fields)

        shop_sku = self._resolve_required_product_sku(row_fields=row_fields)
        parent_sku = self._resolve_optional_representation(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU,
        )
        is_configurable = bool(parent_sku and parent_sku != shop_sku)
        if not is_configurable:
            parent_sku = shop_sku

        name = (
            self._resolve_representation_value(
                row_fields=row_fields,
                representation_type=MiraklProperty.REPRESENTATION_PRODUCT_TITLE,
                offer_data=offer_data,
            )
            or shop_sku
        )
        subtitle = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SUBTITLE,
            offer_data=offer_data,
        )
        description = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION,
            offer_data=offer_data,
        )
        short_description = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SHORT_DESCRIPTION,
            offer_data=offer_data,
        )
        bullet_points = self._collect_bullet_points(row_fields=row_fields)
        ean_code = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_EAN,
            offer_data=offer_data,
        )
        raw_category_value = self._resolve_optional_representation(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_CATEGORY,
        )
        category_code = self._resolve_category_code(
            raw_category_value=raw_category_value,
            offer_data=offer_data,
        )
        currency = str(offer_data.get("currency") or "").strip()
        price = self._resolve_numeric_representation(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRICE,
            offer_data=offer_data,
        )
        rrp = offer_data.get("rrp")
        child_images, parent_images = self._build_images(row_fields=row_fields)
        documents = self._build_documents(row_fields=row_fields)
        properties = self._build_property_entries(
            row_fields=row_fields,
            offer_data=offer_data,
        )
        rule = self._resolve_product_rule(
            category_code=category_code,
            raw_category_value=raw_category_value,
        )
        translations = [
            {
                "language": self.default_language,
                "sales_channel": self.sales_channel,
                "name": name,
                "subtitle": subtitle,
                "description": description,
                "short_description": short_description,
                "url_key": slugify(name) or slugify(parent_sku),
                "bullet_points": bullet_points,
            }
        ]
        child_payload: dict[str, Any] = {
            "sku": shop_sku,
            "name": name,
            "type": Product.SIMPLE,
            "translations": translations,
        }
        if properties:
            child_payload["properties"] = properties
        if child_images:
            child_payload["images"] = child_images
        if documents:
            child_payload["documents"] = documents
        if ean_code:
            child_payload["ean_code"] = ean_code
        if currency and (price is not None or rrp is not None):
            child_payload["prices"] = [{"currency": currency, "price": price, "rrp": rrp}]

        parent_payload = None
        if is_configurable:
            parent_payload = {
                "sku": parent_sku,
                "name": name,
                "type": Product.CONFIGURABLE,
                "translations": translations,
            }
            if parent_images:
                parent_payload["images"] = parent_images
        else:
            parent_images = []

        return MiraklMappedRow(
            shop_sku=shop_sku,
            remote_sku=str(offer_data.get("remote_sku") or "").strip(),
            category_code=category_code,
            rule=rule,
            is_configurable=is_configurable,
            parent_sku=parent_sku,
            parent_payload=parent_payload,
            child_payload=child_payload,
            view_codes=self._normalize_view_codes(offer_data=offer_data),
            offer_data=offer_data,
        )

    def _resolve_required_product_sku(self, *, row_fields: dict[str, str]) -> str:
        value = self._resolve_optional_representation(
            row_fields=row_fields,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
        )
        if value:
            return value
        raise MiraklImportMissingProductSkuError("Mirakl import row is missing product_sku.")

    def _resolve_optional_representation(
        self,
        *,
        row_fields: dict[str, str],
        representation_type: str,
    ) -> str:
        for code, raw_value in row_fields.items():
            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                continue
            if remote_property.representation_type != representation_type:
                continue
            value = str(raw_value or "").strip()
            if value:
                return value
        return ""

    def _resolve_representation_value(
        self,
        *,
        row_fields: dict[str, str],
        representation_type: str,
        offer_data: dict[str, Any],
    ) -> str:
        value = self._resolve_optional_representation(
            row_fields=row_fields,
            representation_type=representation_type,
        )
        if value:
            return value
        fallback = self._get_offer_representation_fallback(
            representation_type=representation_type,
            offer_data=offer_data,
        )
        return str(fallback or "").strip()

    def _resolve_boolean_representation(
        self,
        *,
        row_fields: dict[str, str],
        representation_type: str,
        offer_data: dict[str, Any],
        default: bool,
    ) -> bool:
        value = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=representation_type,
            offer_data=offer_data,
        )
        if value == "":
            fallback = offer_data.get("active")
            if fallback in (None, ""):
                return default
            return self._coerce_boolean(value=fallback)
        return self._coerce_boolean(value=value)

    def _resolve_numeric_representation(
        self,
        *,
        row_fields: dict[str, str],
        representation_type: str,
        offer_data: dict[str, Any],
    ) -> Any:
        value = self._resolve_representation_value(
            row_fields=row_fields,
            representation_type=representation_type,
            offer_data=offer_data,
        )
        if value == "":
            return None
        return value

    def _resolve_category_code(
        self,
        *,
        raw_category_value: str,
        offer_data: dict[str, Any],
    ) -> str:
        offer_category_code = str(offer_data.get("category_code") or "").strip()
        if offer_category_code:
            return offer_category_code

        normalized_candidates = self._build_lookup_candidates(value=raw_category_value)
        direct_remote_id = str(raw_category_value or "").strip()
        if direct_remote_id in self._leaf_category_by_remote_id:
            return direct_remote_id

        for candidate in normalized_candidates:
            remote_id = self._leaf_category_remote_id_by_name.get(candidate)
            if remote_id:
                return remote_id

        for candidate in normalized_candidates:
            product_type = self._product_type_by_name.get(candidate)
            if product_type is None:
                continue
            product_type_category = getattr(product_type, "category", None)
            product_type_category_remote_id = str(getattr(product_type_category, "remote_id", "") or "").strip()
            if product_type_category_remote_id:
                return product_type_category_remote_id

        return ""

    def _get_offer_representation_fallback(
        self,
        *,
        representation_type: str,
        offer_data: dict[str, Any],
    ) -> Any:
        fallback_map = {
            MiraklProperty.REPRESENTATION_PRODUCT_TITLE: offer_data.get("product_name"),
            MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION: offer_data.get("product_description"),
            MiraklProperty.REPRESENTATION_PRODUCT_SHORT_DESCRIPTION: offer_data.get("product_short_description"),
            MiraklProperty.REPRESENTATION_PRODUCT_CATEGORY: offer_data.get("category_code"),
            MiraklProperty.REPRESENTATION_PRICE: offer_data.get("price"),
            MiraklProperty.REPRESENTATION_DISCOUNTED_PRICE: offer_data.get("price"),
            MiraklProperty.REPRESENTATION_CONDITION: offer_data.get("condition"),
            MiraklProperty.REPRESENTATION_LOGISTIC_CLASS: offer_data.get("logistic_class"),
        }
        return fallback_map.get(representation_type, "")

    def _collect_bullet_points(self, *, row_fields: dict[str, str]) -> list[str]:
        bullets: list[str] = []
        for code, raw_value in row_fields.items():
            if not raw_value:
                continue
            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                continue
            if remote_property.representation_type != MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT:
                continue
            bullets.append(str(raw_value).strip())
        return [value for value in bullets if value]

    def _build_images(self, *, row_fields: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        child_images: list[dict[str, Any]] = []
        parent_images: list[dict[str, Any]] = []
        child_seen: set[tuple[str, str]] = set()
        parent_seen: set[str] = set()

        child_sort_order = 0
        parent_sort_order = 0

        for code, raw_value in row_fields.items():
            url = str(raw_value or "").strip()
            if not url:
                continue

            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                continue

            representation_type = remote_property.representation_type
            if representation_type not in {
                MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
                MiraklProperty.REPRESENTATION_IMAGE,
                MiraklProperty.REPRESENTATION_SWATCH_IMAGE,
            }:
                continue

            image_type = Image.COLOR_SHOT if representation_type == MiraklProperty.REPRESENTATION_SWATCH_IMAGE else Image.PACK_SHOT
            child_key = (url, image_type)
            if child_key not in child_seen:
                child_seen.add(child_key)
                child_images.append(
                    {
                        "image_url": url,
                        "type": image_type,
                        "is_main_image": representation_type == MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
                        "sort_order": child_sort_order,
                    }
                )
                child_sort_order += 1

            if representation_type == MiraklProperty.REPRESENTATION_SWATCH_IMAGE:
                continue

            if url in parent_seen:
                continue

            parent_seen.add(url)
            parent_images.append(
                {
                    "image_url": url,
                    "type": Image.PACK_SHOT,
                    "is_main_image": representation_type == MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE,
                    "sort_order": parent_sort_order,
                }
            )
            parent_sort_order += 1

        return child_images, parent_images

    def _build_documents(self, *, row_fields: dict[str, str]) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []
        seen_document_keys: set[tuple[str, str]] = set()

        for code, raw_value in row_fields.items():
            document_url = str(raw_value or "").strip()
            if not document_url:
                continue

            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                continue
            if remote_property.representation_type != MiraklProperty.REPRESENTATION_DOCUMENT:
                continue

            remote_document_type = self._document_type_by_remote_id.get(str(remote_property.code or "").strip())
            if remote_document_type is None or remote_document_type.local_instance is None:
                continue

            document_key = (str(remote_document_type.remote_id or "").strip(), document_url)
            if document_key in seen_document_keys:
                continue
            seen_document_keys.add(document_key)

            documents.append(
                {
                    "document_url": document_url,
                    "title": str(remote_document_type.name or remote_property.name or remote_property.code or "").strip(),
                    "description": str(remote_document_type.description or remote_property.description or "").strip(),
                    "document_type": remote_document_type.local_instance,
                    "document_language": self.default_language,
                    "sort_order": len(documents),
                }
            )

        return documents

    def _build_property_entries(
        self,
        *,
        row_fields: dict[str, str],
        offer_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for code, raw_value in row_fields.items():
            remote_property = self._property_by_code.get(code)
            if remote_property is None:
                continue

            if remote_property.representation_type not in self.PROPERTY_REPRESENTATIONS:
                continue

            local_property = getattr(remote_property, "local_instance", None)
            if local_property is None:
                continue

            effective_value = str(raw_value or "").strip()
            if not effective_value:
                effective_value = self._get_property_offer_fallback(
                    code=code,
                    remote_property=remote_property,
                    offer_data=offer_data,
                )
            if not effective_value:
                effective_value = str(getattr(remote_property, "default_value", "") or "").strip()
            if not effective_value:
                continue

            entry = self._build_property_entry(
                local_property=local_property,
                remote_property=remote_property,
                value=effective_value,
            )
            if entry is not None:
                results.append(entry)

        return results

    def _build_property_entry(
        self,
        *,
        local_property: Property,
        remote_property: MiraklProperty,
        value: Any,
    ) -> dict[str, Any] | None:
        property_type = local_property.type
        entry: dict[str, Any] = {"property": local_property}

        if property_type == Property.TYPES.SELECT:
            mapped_entry = self._map_select_value(
                remote_property=remote_property,
                value=value,
                multiple=False,
            )
            if mapped_entry is None:
                return None
            entry.update(mapped_entry)
            return entry

        if property_type == Property.TYPES.MULTISELECT:
            mapped_entry = self._map_select_value(
                remote_property=remote_property,
                value=value,
                multiple=True,
            )
            if mapped_entry is None:
                return None
            entry.update(mapped_entry)
            return entry

        entry["value"] = self._normalize_scalar_value(
            value=value,
            property_type=property_type,
        )
        return entry

    def _map_select_value(
        self,
        *,
        remote_property: MiraklProperty,
        value: Any,
        multiple: bool,
    ) -> dict[str, Any] | None:
        if not self._requires_remote_select_mapping(remote_property=remote_property):
            normalized = self._normalize_scalar_value(
                value=value,
                property_type=Property.TYPES.MULTISELECT if multiple else Property.TYPES.SELECT,
            )
            return {"value": normalized}

        if multiple:
            values = self._normalize_multi_value(value=value)
            mapped_ids: list[int] = []
            for item in values:
                mapped = self._select_value_lookup.get((remote_property.id, item.lower()))
                if mapped is not None and mapped.local_instance_id:
                    mapped_ids.append(mapped.local_instance_id)
            if not mapped_ids:
                return None
            return {"value": mapped_ids, "value_is_id": True}

        normalized = str(value or "").strip().lower()
        if not normalized:
            return None
        mapped = self._select_value_lookup.get((remote_property.id, normalized))
        if mapped is None or not mapped.local_instance_id:
            return None
        return {"value": mapped.local_instance_id, "value_is_id": True}

    def _requires_remote_select_mapping(self, *, remote_property: MiraklProperty) -> bool:
        original_type = str(getattr(remote_property, "original_type", "") or "").upper()
        remote_type = str(getattr(remote_property, "type", "") or "").upper()
        if original_type in {Property.TYPES.SELECT, Property.TYPES.MULTISELECT}:
            return True
        if remote_type in {Property.TYPES.SELECT, Property.TYPES.MULTISELECT}:
            return True
        return MiraklPropertySelectValue.objects.filter(
            sales_channel=self.sales_channel,
            remote_property=remote_property,
        ).exists()

    def _normalize_scalar_value(self, *, value: Any, property_type: str) -> Any:
        if property_type == Property.TYPES.BOOLEAN:
            return self._coerce_boolean(value=value)
        if property_type == Property.TYPES.INT:
            return int(float(str(value).strip()))
        if property_type == Property.TYPES.FLOAT:
            return float(str(value).strip())
        if property_type == Property.TYPES.MULTISELECT:
            return self._normalize_multi_value(value=value)
        return value

    def _normalize_multi_value(self, *, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        separator = getattr(self.sales_channel, "list_of_multiple_values_separator", None) or ","
        raw = str(value or "").strip()
        if not raw:
            return []
        if separator in raw:
            return [chunk.strip() for chunk in raw.split(separator) if chunk.strip()]
        return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]

    def _coerce_boolean(self, *, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value or "").strip().lower()
        return normalized in {"1", "true", "yes", "y"}

    def _get_property_offer_fallback(
        self,
        *,
        code: str,
        remote_property: MiraklProperty,
        offer_data: dict[str, Any],
    ) -> str:
        code_fallbacks = {
            "product_brand": offer_data.get("brand"),
            "brand": offer_data.get("brand"),
            "internal_description": offer_data.get("product_short_description"),
        }
        fallback = code_fallbacks.get(str(code or "").strip().lower())
        if fallback not in (None, ""):
            return str(fallback).strip()

        if remote_property.representation_type == MiraklProperty.REPRESENTATION_CONDITION:
            return str(offer_data.get("condition") or "").strip()
        if remote_property.representation_type == MiraklProperty.REPRESENTATION_LOGISTIC_CLASS:
            return str(offer_data.get("logistic_class") or "").strip()
        return ""

    def _normalize_view_codes(self, *, offer_data: dict[str, Any]) -> list[str]:
        channels = offer_data.get("channels") or []
        if not isinstance(channels, list):
            return []
        results: list[str] = []
        for item in channels:
            value = str(item or "").strip()
            if value and value not in results:
                results.append(value)
        return results

    def _resolve_product_rule(self, *, category_code: str, raw_category_value: str):
        if category_code:
            product_type = self._product_type_by_remote_id.get(category_code)
            if product_type is not None and product_type.local_instance_id:
                return product_type.local_instance

        direct_remote_match = self._product_type_by_remote_id.get(str(raw_category_value or "").strip())
        if direct_remote_match is not None and direct_remote_match.local_instance_id:
            return direct_remote_match.local_instance

        for candidate in self._build_lookup_candidates(value=raw_category_value):
            product_type = self._product_type_by_name.get(candidate)
            if product_type is not None and product_type.local_instance_id:
                return product_type.local_instance
        return None

    def _build_lookup_candidates(self, *, value: str) -> list[str]:
        raw_value = str(value or "").strip()
        if not raw_value:
            return []

        candidates: list[str] = []
        for candidate in [raw_value, raw_value.split("/")[-1].strip()]:
            normalized = self._normalize_lookup_token(value=candidate)
            if normalized and normalized not in candidates:
                candidates.append(normalized)
        return candidates

    def _normalize_lookup_token(self, *, value: Any) -> str:
        return str(value or "").strip().lower()

    def _ensure_select_value_lookup_for_headers(self, *, row_fields: dict[str, str]) -> None:
        relevant_property_ids = {
            remote_property.id
            for code in row_fields.keys()
            if (remote_property := self._property_by_code.get(code)) is not None
        }
        property_ids_to_load = relevant_property_ids - self._loaded_select_value_property_ids
        if not property_ids_to_load:
            return

        self._loaded_select_value_property_ids.update(property_ids_to_load)
        for key, item in self._build_select_value_lookup(
            remote_property_ids=property_ids_to_load,
        ).items():
            if key not in self._select_value_lookup:
                self._select_value_lookup[key] = item

    def _build_select_value_lookup(
        self,
        *,
        remote_property_ids: set[int] | None = None,
    ) -> dict[tuple[int, str], MiraklPropertySelectValue]:
        lookup: dict[tuple[int, str], MiraklPropertySelectValue] = {}
        queryset = MiraklPropertySelectValue.objects.filter(sales_channel=self.sales_channel)
        if remote_property_ids is not None:
            if not remote_property_ids:
                return lookup
            queryset = queryset.filter(remote_property_id__in=remote_property_ids)

        queryset = queryset.select_related(
            "local_instance",
            "remote_property",
        ).order_by("id")
        for item in queryset:
            candidates = [item.value, item.code]
            for candidate in candidates:
                normalized = str(candidate or "").strip().lower()
                key = (item.remote_property_id, normalized)
                if normalized and key not in lookup:
                    lookup[key] = item
        return lookup
