from __future__ import annotations

from typing import Mapping

OFFER_HEADER_PREFIX = "offer-"
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


def normalize_offer_external_key(*, external_key: str) -> str:
    normalized_key = str(external_key or "").strip()
    if normalized_key.startswith(OFFER_HEADER_PREFIX):
        return normalized_key[len(OFFER_HEADER_PREFIX):]
    return normalized_key


def build_offer_field_key(*, external_key: str) -> str:
    return f"{OFFER_FIELD_PREFIX}{normalize_offer_external_key(external_key=external_key)}"


def strip_offer_field_key(*, internal_key: str) -> str:
    normalized_key = str(internal_key or "").strip()
    if normalized_key.startswith(OFFER_FIELD_PREFIX):
        return normalized_key[len(OFFER_FIELD_PREFIX):]
    return normalized_key


def is_offer_field_header(*, header: str) -> bool:
    return normalize_offer_external_key(external_key=header) in OFFER_FIELD_KEYS


def is_explicit_offer_field_header(*, header: str) -> bool:
    normalized_header = str(header or "").strip()
    return normalized_header.startswith(OFFER_HEADER_PREFIX) and is_offer_field_header(header=normalized_header)


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
