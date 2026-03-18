from __future__ import annotations

import json
import re
from typing import Any


def normalize_mirakl_type_parameters(*, raw_value: Any) -> list[dict[str, Any]]:
    parsed_value = _parse_raw_value(raw_value=raw_value)
    if isinstance(parsed_value, list):
        return [entry for entry in parsed_value if isinstance(entry, dict)]
    if isinstance(parsed_value, dict):
        return [parsed_value]
    return []


def get_mirakl_type_parameter_value(*, raw_value: Any, name: str) -> str:
    normalized_name = _normalize_name(value=name)
    if not normalized_name:
        return ""
    for entry in normalize_mirakl_type_parameters(raw_value=raw_value):
        if _normalize_name(value=entry.get("name")) != normalized_name:
            continue
        resolved_value = str(entry.get("value") or "").strip()
        if resolved_value:
            return resolved_value
    return ""


def _parse_raw_value(*, raw_value: Any) -> Any:
    if raw_value in (None, ""):
        return []
    if isinstance(raw_value, (list, dict)):
        return raw_value
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return []
        try:
            return json.loads(stripped)
        except (TypeError, ValueError):
            return []
    return []


def _normalize_name(*, value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
