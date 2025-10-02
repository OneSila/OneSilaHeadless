"""Shared helper utilities for the eBay sales channel integration."""

from __future__ import annotations

from typing import Any, Iterable


def get_parent_skus(*, product_data: Any) -> set[str]:
    """Return the parent SKU identifiers declared on an inventory payload."""

    if not isinstance(product_data, dict):
        return set()

    parent_skus: set[str] = set()

    for key in ("group_ids", "inventory_item_group_keys"):
        values = product_data.get(key)
        if values is None:
            continue

        iterable: Iterable[Any]
        if isinstance(values, str) or not isinstance(values, (list, tuple, set)):
            iterable = [values]
        else:
            iterable = values

        for value in iterable:
            if value is None:
                continue

            normalized = value.strip() if isinstance(value, str) else str(value)
            if not normalized:
                continue

            parent_skus.add(normalized)

    return parent_skus


def get_is_product_variation(*, product_data: Any) -> tuple[bool, set[str]]:
    """Return whether the payload references a variation and its parent SKUs."""

    parent_skus = get_parent_skus(product_data=product_data)

    return bool(parent_skus), parent_skus
