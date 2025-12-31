"""Utility helpers for Shein product import parsing."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_text(*, value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_identifier(*, value: Any) -> str | None:
    return normalize_text(value=value)


def normalize_id_list(*, value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = value
    else:
        raw = [value]
    ids: list[str] = []
    for entry in raw:
        normalized = normalize_identifier(value=entry)
        if not normalized or normalized in {"0", "0.0"}:
            continue
        ids.append(normalized)
    return ids


def coerce_decimal(*, value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
