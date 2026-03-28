from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from django.utils import timezone
from django.utils.text import slugify

from sales_channels.integrations.mirakl.models import MiraklProperty, MiraklPublicDefinition


PUBLIC_DEFINITIONS_FILENAME_RE = re.compile(r"^\d{2}_\d{2}_\d{4}_[A-Za-z0-9_-]+\.json$")
PUBLIC_DEFINITIONS_DIR = Path(__file__).resolve().parent
PUBLIC_DEFINITION_FIELDS = (
    "hostname",
    "property_code",
    "representation_type",
    "language",
    "default_value",
    "yes_text_value",
    "no_text_value",
)
ALLOWED_REPRESENTATION_TYPES = {
    choice[0]
    for choice in MiraklProperty.REPRESENTATION_TYPE_CHOICES
}


def get_public_definitions_directory(*, create: bool = False) -> Path:
    directory = PUBLIC_DEFINITIONS_DIR
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_export_name(*, name: str) -> str:
    normalized = slugify(str(name or "")).replace("-", "_").strip("_")
    if not normalized:
        raise ValueError("Name must contain at least one alphanumeric character.")
    return normalized


def build_export_filename(*, name: str, export_date: date | None = None) -> str:
    normalized_name = normalize_export_name(name=name)
    current_date = export_date or timezone.localdate()
    return f"{current_date.strftime('%d_%m_%Y')}_{normalized_name}.json"


def is_valid_public_definitions_filename(*, file_name: str) -> bool:
    normalized = Path(str(file_name or "")).name
    return bool(PUBLIC_DEFINITIONS_FILENAME_RE.fullmatch(normalized))


def get_public_definitions_file_path(*, file_name: str, create_directory: bool = False) -> Path:
    normalized = Path(str(file_name or "")).name
    if normalized != str(file_name or ""):
        raise ValueError("File name must not include directory segments.")
    if not is_valid_public_definitions_filename(file_name=normalized):
        raise ValueError("File name must match dd_mm_yyyy_name_parameter.json.")
    return get_public_definitions_directory(create=create_directory) / normalized


def serialize_public_definition(*, definition: MiraklPublicDefinition) -> dict[str, Any]:
    return {
        "hostname": definition.hostname,
        "property_code": definition.property_code,
        "representation_type": definition.representation_type,
        "language": definition.language,
        "default_value": definition.default_value,
        "yes_text_value": definition.yes_text_value,
        "no_text_value": definition.no_text_value,
    }


def export_public_definitions_to_file(*, file_path: Path, hostname: str | None = None) -> int:
    queryset = MiraklPublicDefinition.objects.all()
    if hostname:
        queryset = queryset.filter(hostname=hostname)

    definitions = [
        serialize_public_definition(definition=definition)
        for definition in queryset.order_by("hostname", "property_code")
    ]
    file_path.write_text(
        json.dumps(definitions, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    return len(definitions)


def import_public_definitions_from_file(*, file_path: Path, skip_existing: bool = False, hostname: str | None = None) -> dict[str, int]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Public definitions file must contain a JSON list.")

    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
    }

    for index, raw_definition in enumerate(payload, start=1):
        if not isinstance(raw_definition, dict):
            raise ValueError(f"Definition #{index} must be a JSON object.")

        cleaned_definition = clean_public_definition_payload(payload=raw_definition)
        if hostname and cleaned_definition["hostname"] != hostname:
            continue

        definition_hostname = cleaned_definition["hostname"]
        property_code = cleaned_definition["property_code"]
        defaults = {
            field_name: cleaned_definition[field_name]
            for field_name in PUBLIC_DEFINITION_FIELDS
            if field_name not in {"hostname", "property_code"}
        }

        definition, created = MiraklPublicDefinition.objects.get_or_create(
            hostname=definition_hostname,
            property_code=property_code,
            defaults=defaults,
        )
        if created:
            stats["created"] += 1
            continue

        if skip_existing:
            stats["skipped"] += 1
            continue

        updated_fields: list[str] = []
        for field_name, value in defaults.items():
            if getattr(definition, field_name) == value:
                continue
            setattr(definition, field_name, value)
            updated_fields.append(field_name)

        if updated_fields:
            definition.save(update_fields=updated_fields)
            stats["updated"] += 1
            continue

        stats["skipped"] += 1

    return stats


def clean_public_definition_payload(*, payload: dict[str, Any]) -> dict[str, str | None]:
    cleaned_definition = {
        "hostname": _normalize_required_text(value=payload.get("hostname"), field_name="hostname"),
        "property_code": _normalize_required_text(value=payload.get("property_code"), field_name="property_code"),
        "representation_type": _normalize_representation_type(value=payload.get("representation_type")),
        "language": _normalize_optional_text(value=payload.get("language")),
        "default_value": _normalize_text(value=payload.get("default_value")),
        "yes_text_value": _normalize_text(value=payload.get("yes_text_value")),
        "no_text_value": _normalize_text(value=payload.get("no_text_value")),
    }
    return cleaned_definition


def _normalize_required_text(*, value: Any, field_name: str) -> str:
    normalized = _normalize_text(value=value)
    if not normalized:
        raise ValueError(f"Field '{field_name}' is required.")
    return normalized


def _normalize_optional_text(*, value: Any) -> str | None:
    normalized = _normalize_text(value=value)
    return normalized or None


def _normalize_text(*, value: Any) -> str:
    return str(value or "").strip()


def _normalize_representation_type(*, value: Any) -> str:
    normalized = _normalize_required_text(
        value=value,
        field_name="representation_type",
    )
    if normalized not in ALLOWED_REPRESENTATION_TYPES:
        raise ValueError(f"Invalid representation_type '{normalized}'.")
    return normalized
