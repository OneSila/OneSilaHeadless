"""Helpers for Shein product attribute parsing."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .product_utils import normalize_identifier, normalize_text


def extract_dimension_records(
    *,
    dimension_records: Iterable[Any],
    sale_attribute_map: dict[str, str],
    apply_global_only: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for entry in dimension_records:
        if not isinstance(entry, Mapping):
            continue
        attribute_id = normalize_identifier(value=entry.get("attributeId") or entry.get("attribute_id"))
        if not attribute_id:
            continue
        additions = entry.get("dimensionAttributeAdditionList") or entry.get("dimension_attribute_addition_list") or []
        if not isinstance(additions, Iterable):
            continue

        for addition in additions:
            if not isinstance(addition, Mapping):
                continue
            relate_id = normalize_identifier(
                value=addition.get("relateSaleAttributeId") or addition.get("relate_sale_attribute_id")
            )
            relate_value_id = normalize_identifier(
                value=addition.get("relateSaleAttributeValueId") or addition.get("relate_sale_attribute_value_id")
            )
            if apply_global_only and (relate_id not in (None, "0") or relate_value_id not in (None, "0")):
                continue
            if not apply_global_only and sale_attribute_map:
                mapped_value = sale_attribute_map.get(relate_id or "")
                if relate_id not in (None, "0") and mapped_value != relate_value_id:
                    continue
            value = addition.get("additionValue") or addition.get("addition_value")
            normalized_value = normalize_text(value=value)
            if normalized_value is None:
                continue
            record = {
                "attributeId": attribute_id,
                "attributeValue": normalized_value,
            }
            records.append(record)
            if apply_global_only:
                break
    return records
