from __future__ import annotations

from typing import Mapping

OFFER_FIELD_PREFIX = "offer__"
OFFER_FIELD_KEYS = (
    "sku",
    "product-id",
    "product-id-type",
    "description",
    "internal-description",
    "price",
    "price-additional-info",
    "quantity",
    "min-quantity-alert",
    "state",
    "available-start-date",
    "available-end-date",
    "logistic-class",
    "discount-price",
    "discount-start-date",
    "discount-end-date",
    "leadtime-to-ship",
    "update-delete",
)


def build_offer_field_key(*, external_key: str) -> str:
    return f"{OFFER_FIELD_PREFIX}{str(external_key or '').strip()}"


def strip_offer_field_key(*, internal_key: str) -> str:
    normalized_key = str(internal_key or "").strip()
    if normalized_key.startswith(OFFER_FIELD_PREFIX):
        return normalized_key[len(OFFER_FIELD_PREFIX):]
    return normalized_key


def is_offer_field_header(*, header: str) -> bool:
    return str(header or "").strip() in OFFER_FIELD_KEYS


def add_offer_field_aliases(*, row: Mapping[str, str]) -> dict[str, str]:
    expanded_row = {
        str(key): value
        for key, value in row.items()
    }
    for key, value in list(expanded_row.items()):
        if not key.startswith(OFFER_FIELD_PREFIX):
            continue
        expanded_row.setdefault(strip_offer_field_key(internal_key=key), value)
    return expanded_row
