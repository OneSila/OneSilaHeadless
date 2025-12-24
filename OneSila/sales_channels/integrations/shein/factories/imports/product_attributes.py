"""Attribute parsing helpers for Shein product imports."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from properties.models import Property
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinInternalPropertyOption,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
)

from .product_attribute_helpers import extract_dimension_records
from .product_utils import normalize_id_list, normalize_identifier, normalize_text


class SheinProductImportAttributeParser:
    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel
        self.multi_tenant_company = sales_channel.multi_tenant_company
        self._internal_property_cache: dict[str, SheinInternalProperty | None] = {}
        self._product_type_item_cache: dict[str, dict[str, SheinProductTypeItem]] = {}
        self._select_value_cache: dict[tuple[int, str], SheinPropertySelectValue | None] = {}

    def parse_attributes(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        product_type_id: str | None,
        is_variation: bool,
        include_sku_fields: bool,
        language_code: str | None,
    ) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
        attributes: list[dict[str, Any]] = []
        mirror_map: dict[int, dict[str, Any]] = {}

        attributes.extend(
            self._parse_internal_properties(
                spu_payload=spu_payload,
                skc_payload=skc_payload,
                sku_payload=sku_payload,
                include_sku_fields=include_sku_fields,
            )
        )

        type_item_map = self._get_product_type_items(product_type_id=product_type_id)

        if not is_variation:
            attribute_records = spu_payload.get("productAttributeInfoList") or spu_payload.get("product_attribute_info_list") or []
            for record in attribute_records:
                self._ingest_attribute_record(
                    record=record,
                    type_item_map=type_item_map,
                    attributes=attributes,
                    mirror_map=mirror_map,
                    language_code=language_code,
                )

            dimension_records = extract_dimension_records(
                dimension_records=spu_payload.get("dimensionAttributeInfoList")
                or spu_payload.get("dimension_attribute_info_list")
                or [],
                sale_attribute_map={},
                apply_global_only=True,
            )
            for record in dimension_records:
                self._ingest_attribute_record(
                    record=record,
                    type_item_map=type_item_map,
                    attributes=attributes,
                    mirror_map=mirror_map,
                    language_code=language_code,
                )

        sale_attribute_map = self._build_sale_attribute_map(
            skc_payload=skc_payload,
            sku_payload=sku_payload,
            type_item_map=type_item_map,
            attributes=attributes,
            mirror_map=mirror_map,
            language_code=language_code,
            include=is_variation or include_sku_fields,
        )

        if sale_attribute_map:
            dimension_records = extract_dimension_records(
                dimension_records=spu_payload.get("dimensionAttributeInfoList")
                or spu_payload.get("dimension_attribute_info_list")
                or [],
                sale_attribute_map=sale_attribute_map,
                apply_global_only=False,
            )
            for record in dimension_records:
                self._ingest_attribute_record(
                    record=record,
                    type_item_map=type_item_map,
                    attributes=attributes,
                    mirror_map=mirror_map,
                    language_code=language_code,
                )

        return attributes, mirror_map

    def _get_internal_property(self, *, code: str) -> SheinInternalProperty | None:
        if not code:
            return None
        cached = self._internal_property_cache.get(code)
        if cached is not None:
            return cached
        internal_property = (
            SheinInternalProperty.objects.filter(
                sales_channel=self.sales_channel,
                code=code,
            )
            .select_related("local_instance")
            .prefetch_related("options__local_instance")
            .first()
        )
        self._internal_property_cache[code] = internal_property
        return internal_property

    def _parse_internal_properties(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        include_sku_fields: bool,
    ) -> list[dict[str, Any]]:
        attributes: list[dict[str, Any]] = []

        brand_code = normalize_identifier(value=spu_payload.get("brandCode") or spu_payload.get("brand_code"))
        if brand_code:
            payload = self._build_internal_property_payload(code="brand_code", value=brand_code)
            if payload:
                attributes.append(payload)

        supplier_code = normalize_text(
            value=(skc_payload or {}).get("supplierCode") or (skc_payload or {}).get("supplier_code")
        ) or normalize_text(value=spu_payload.get("supplierCode") or spu_payload.get("supplier_code"))
        if supplier_code:
            payload = self._build_internal_property_payload(code="supplier_code", value=supplier_code)
            if payload:
                attributes.append(payload)

        if include_sku_fields and isinstance(sku_payload, Mapping):
            package_type = sku_payload.get("packageType") or sku_payload.get("package_type")
            if package_type not in (None, "", []):
                payload = self._build_internal_property_payload(code="package_type", value=package_type)
                if payload:
                    attributes.append(payload)

            for field, code in (
                ("length", "length"),
                ("width", "width"),
                ("height", "height"),
                ("weight", "weight"),
            ):
                raw = sku_payload.get(field)
                normalized = normalize_text(value=raw)
                if normalized:
                    payload = self._build_internal_property_payload(code=code, value=normalized)
                    if payload:
                        attributes.append(payload)

            quantity_unit = sku_payload.get("quantityUnit") or sku_payload.get("quantity_unit")
            quantity_value = sku_payload.get("quantity")
            if quantity_unit not in (None, "", []) and quantity_value not in (None, "", []):
                unit_payload = self._build_internal_property_payload(code="quantity_info__unit", value=quantity_unit)
                if unit_payload:
                    attributes.append(unit_payload)
                qty_payload = self._build_internal_property_payload(code="quantity_info__quantity", value=quantity_value)
                if qty_payload:
                    attributes.append(qty_payload)

        return attributes

    def _build_internal_property_payload(self, *, code: str, value: Any) -> dict[str, Any] | None:
        internal_property = self._get_internal_property(code=code)
        if internal_property is None or internal_property.local_instance is None:
            return None

        prop = internal_property.local_instance
        if prop.type == Property.TYPES.SELECT:
            option = None
            if internal_property.options.exists():
                option = (
                    SheinInternalPropertyOption.objects.filter(
                        internal_property=internal_property,
                        value=str(value).strip(),
                    )
                    .select_related("local_instance")
                    .first()
                )
            if option and option.local_instance:
                return {
                    "property": prop,
                    "value": option.local_instance.id,
                    "value_is_id": True,
                }
        return {
            "property": prop,
            "value": value,
        }

    def _get_product_type_items(self, *, product_type_id: str | None) -> dict[str, SheinProductTypeItem]:
        if not product_type_id:
            return {}
        normalized = str(product_type_id).strip()
        if not normalized:
            return {}
        cached = self._product_type_item_cache.get(normalized)
        if cached is not None:
            return cached
        items = (
            SheinProductTypeItem.objects.filter(
                product_type__sales_channel=self.sales_channel,
                product_type__remote_id=normalized,
            )
            .select_related("property", "property__local_instance", "local_instance")
        )
        mapped = {
            str(item.property.remote_id): item
            for item in items
            if item.property_id and item.property.remote_id not in (None, "")
        }
        self._product_type_item_cache[normalized] = mapped
        return mapped

    def _normalize_attribute_record(
        self,
        *,
        record: Mapping[str, Any],
        value_override: Any | None = None,
    ) -> dict[str, Any] | None:
        attribute_id = normalize_identifier(value=record.get("attributeId") or record.get("attribute_id"))
        if not attribute_id:
            return None
        value_ids = normalize_id_list(value=record.get("attributeValueId") or record.get("attribute_value_id"))
        value_names: list[str] = []
        raw_names = record.get("attributeValueMultiList") or record.get("attribute_value_multi_list") or []
        if isinstance(raw_names, Iterable):
            for entry in raw_names:
                if not isinstance(entry, Mapping):
                    continue
                name = normalize_text(value=entry.get("attributeValueName") or entry.get("attribute_value_name"))
                if name and name not in value_names:
                    value_names.append(name)

        custom_value = value_override
        if custom_value is None:
            custom_value = record.get("attributeValue") or record.get("attribute_extra_value")
        if custom_value is not None:
            custom_value = normalize_text(value=custom_value)

        return {
            "attribute_id": attribute_id,
            "value_ids": value_ids,
            "value_names": value_names,
            "custom_value": custom_value,
        }

    def _resolve_select_value(
        self,
        *,
        remote_property: SheinProperty,
        remote_value_id: str,
    ) -> SheinPropertySelectValue | None:
        cache_key = (remote_property.id, remote_value_id)
        cached = self._select_value_cache.get(cache_key)
        if cached is not None:
            return cached
        instance = (
            SheinPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
                remote_id=remote_value_id,
            )
            .select_related("local_instance")
            .first()
        )
        self._select_value_cache[cache_key] = instance
        return instance

    def _ingest_attribute_record(
        self,
        *,
        record: Mapping[str, Any],
        type_item_map: dict[str, SheinProductTypeItem],
        attributes: list[dict[str, Any]],
        mirror_map: dict[int, dict[str, Any]],
        language_code: str | None,
    ) -> None:
        normalized = self._normalize_attribute_record(record=record)
        if not normalized:
            return

        attribute_id = normalized["attribute_id"]
        type_item = type_item_map.get(attribute_id)
        remote_property = type_item.property if type_item else None
        if remote_property is None:
            remote_property = (
                SheinProperty.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=attribute_id,
                )
                .select_related("local_instance")
                .first()
            )

        payload, mirror = self._build_property_payload(
            normalized=normalized,
            remote_property=remote_property,
            type_item=type_item,
            language_code=language_code,
        )

        if payload:
            attributes.append(payload)
        if mirror:
            mirror_map[mirror["local_property_id"]] = mirror

    def _build_property_payload(
        self,
        *,
        normalized: dict[str, Any],
        remote_property: SheinProperty | None,
        type_item: SheinProductTypeItem | None,
        language_code: str | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if remote_property is None or remote_property.local_instance is None:
            return None, None

        local_property = remote_property.local_instance
        allow_custom = bool(
            remote_property.allows_unmapped_values
            and (getattr(type_item, "allows_unmapped_values", True))
        )

        value_ids = normalized["value_ids"]
        value_names = list(normalized["value_names"])
        custom_value = normalized["custom_value"]

        mapped_ids: list[int] = []
        for value_id in value_ids:
            remote_value = self._resolve_select_value(
                remote_property=remote_property,
                remote_value_id=value_id,
            )
            if remote_value and remote_value.local_instance:
                mapped_ids.append(remote_value.local_instance.id)
            elif remote_value:
                label = remote_value.value or remote_value.value_en
                if label and label not in value_names:
                    value_names.append(label)

        payload: dict[str, Any] | None = None

        if local_property.type == Property.TYPES.SELECT:
            if mapped_ids:
                payload = {
                    "property": local_property,
                    "value": mapped_ids[0],
                    "value_is_id": True,
                }
            elif allow_custom and (custom_value or value_names):
                payload = {
                    "property": local_property,
                    "value": custom_value or value_names[0],
                }

        elif local_property.type == Property.TYPES.MULTISELECT:
            if mapped_ids:
                payload = {
                    "property": local_property,
                    "value": mapped_ids,
                    "value_is_id": True,
                }
            elif allow_custom and (custom_value or value_names):
                payload = {
                    "property": local_property,
                    "value": value_names or ([custom_value] if custom_value else []),
                }

        else:
            value = custom_value or (value_names[0] if value_names else None)
            if value not in (None, ""):
                payload = {
                    "property": local_property,
                    "value": value,
                }

        mirror_payload = self._build_remote_payload(
            normalized=normalized,
            type_item=type_item,
            language_code=language_code,
        )
        mirror = None
        if mirror_payload:
            mirror = {
                "remote_property": remote_property,
                "remote_value": json.dumps(mirror_payload, sort_keys=True),
                "local_property_id": local_property.id,
            }

        return payload, mirror

    def _build_remote_payload(
        self,
        *,
        normalized: dict[str, Any],
        type_item: SheinProductTypeItem | None,
        language_code: str | None,
    ) -> dict[str, Any] | None:
        attribute_type = getattr(type_item, "attribute_type", None)
        attribute_id = normalized.get("attribute_id")
        if not attribute_id:
            return None

        value_ids = normalized.get("value_ids") or []
        value_names = normalized.get("value_names") or []
        custom_value = normalized.get("custom_value")

        payload: dict[str, Any] = {"attribute_id": attribute_id}
        if attribute_type:
            payload["attribute_type"] = attribute_type
        if value_ids:
            payload["attribute_value_id"] = value_ids if len(value_ids) > 1 else value_ids[0]
        if custom_value or value_names:
            payload["attribute_extra_value"] = custom_value or value_names
            if attribute_type == SheinProductTypeItem.AttributeType.SALES:
                payload["custom_attribute_value"] = custom_value or value_names
        if language_code:
            payload["language"] = language_code

        return {k: v for k, v in payload.items() if v not in (None, "", [], {})}

    def _build_sale_attribute_map(
        self,
        *,
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        type_item_map: dict[str, SheinProductTypeItem],
        attributes: list[dict[str, Any]],
        mirror_map: dict[int, dict[str, Any]],
        language_code: str | None,
        include: bool,
    ) -> dict[str, str]:
        sale_attribute_map: dict[str, str] = {}
        if not include:
            return sale_attribute_map

        records: list[Mapping[str, Any]] = []
        if isinstance(skc_payload, Mapping):
            records.append(
                {
                    "attributeId": skc_payload.get("attributeId") or skc_payload.get("attribute_id"),
                    "attributeValueId": skc_payload.get("attributeValueId") or skc_payload.get("attribute_value_id"),
                    "attributeValueMultiList": skc_payload.get("attributeValueMultiList")
                    or skc_payload.get("attribute_value_multi_list"),
                }
            )
        if isinstance(sku_payload, Mapping):
            for entry in sku_payload.get("saleAttributeList") or sku_payload.get("sale_attribute_list") or []:
                if isinstance(entry, Mapping):
                    records.append(entry)

        for record in records:
            normalized = self._normalize_attribute_record(record=record)
            if not normalized:
                continue
            attribute_id = normalized["attribute_id"]
            value_ids = normalized["value_ids"]
            if value_ids:
                sale_attribute_map[attribute_id] = value_ids[0]
            self._ingest_attribute_record(
                record=record,
                type_item_map=type_item_map,
                attributes=attributes,
                mirror_map=mirror_map,
                language_code=language_code,
            )

        return sale_attribute_map
