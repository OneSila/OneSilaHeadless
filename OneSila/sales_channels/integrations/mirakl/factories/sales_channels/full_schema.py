from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

from properties.models import Property

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklInternalProperty,
    MiraklInternalPropertyOption,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklSalesChannelView,
)


logger = logging.getLogger(__name__)


class MiraklFullSchemaSyncFactory(GetMiraklAPIMixin):
    """Fetch and mirror the Mirakl schema metadata."""

    def __init__(self, *, sales_channel, import_process=None):
        self.sales_channel = sales_channel
        self.import_process = import_process
        self._inline_property_values: dict[str, list[dict[str, Any]]] = {}
        self._value_list_labels: dict[str, str] = {}
        self.summary_data = {
            "internal_properties": 0,
            "internal_property_options": 0,
            "document_types": 0,
            "categories": 0,
            "properties": 0,
            "product_type_items": 0,
            "property_applicabilities": 0,
            "property_select_values": 0,
        }
        self._progress_total = 0
        self._progress_processed = 0

    def run(self) -> dict[str, int]:
        additional_fields = self._get_additional_fields()
        document_types = self._get_document_types()
        hierarchies = self._get_hierarchies()
        attributes = self._get_attributes()
        value_lists = self._get_value_lists()

        self._prepare_progress(
            additional_fields=additional_fields,
            document_types=document_types,
            hierarchies=hierarchies,
            attributes=attributes,
            value_lists=value_lists,
        )

        self.sync_internal_properties(additional_fields=additional_fields)
        self.sync_document_types(document_types=document_types)
        self.sync_categories(hierarchies=hierarchies)
        self.sync_properties(attributes=attributes)
        self.sync_select_values(value_lists=value_lists)
        self._save_summary()
        return self.summary_data

    def _get_additional_fields(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/additional_fields")
        return self._normalize_records(response.get("additional_fields"))

    def _get_document_types(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/documents")
        return self._normalize_records(response.get("documents"))

    def _get_hierarchies(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/hierarchies")
        return self._normalize_records(response.get("hierarchies"))

    def _get_attributes(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(
            path="/api/products/attributes",
            params={"all_operator_attributes": True},
        )
        return self._normalize_records(response.get("attributes"))

    def _get_value_lists(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/values_lists")
        return self._normalize_records(response.get("values_lists"))

    def _prepare_progress(
        self,
        *,
        additional_fields: list[dict[str, Any]],
        document_types: list[dict[str, Any]],
        hierarchies: list[dict[str, Any]],
        attributes: list[dict[str, Any]],
        value_lists: list[dict[str, Any]],
    ) -> None:
        value_count = 0
        for value_list in value_lists:
            value_count += len(self._normalize_records(value_list.get("values")))
        for attribute in attributes:
            if attribute.get("values_list"):
                continue
            value_count += len(self._normalize_records(attribute.get("values")))

        self._progress_total = max(
            1,
            len(additional_fields) + len(document_types) + len(hierarchies) + len(attributes) + value_count,
        )

        if self.import_process is None:
            return

        self.import_process.total_records = self._progress_total
        self.import_process.processed_records = 0
        self.import_process.percentage = 0
        self.import_process.save(update_fields=["total_records", "processed_records", "percentage"])

    def _increment_progress(self, *, amount: int = 1) -> None:
        self._progress_processed += amount
        if self.import_process is None:
            return

        percentage = min(
            99,
            math.floor((self._progress_processed / max(1, self._progress_total)) * 100),
        )
        self.import_process.processed_records = min(self._progress_processed, self._progress_total)
        self.import_process.percentage = percentage
        self.import_process.save(update_fields=["processed_records", "percentage"])

    def _save_summary(self) -> None:
        if self.import_process is None:
            return

        self.import_process.summary_data = self.summary_data
        self.import_process.save(update_fields=["summary_data"])

    def sync_internal_properties(self, *, additional_fields: list[dict[str, Any]]) -> None:
        condition_code = self._resolve_condition_code(additional_fields=additional_fields)

        for item in additional_fields:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            accepted_values = self._parse_accepted_values(item.get("accepted_values"))
            property_type = self._map_remote_type(
                remote_type=item.get("type"),
                has_values=bool(accepted_values),
            )
            internal_property, _ = MiraklInternalProperty.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                code=code,
                defaults={
                    "type": property_type,
                },
            )
            internal_property.code = code
            internal_property.name = self._clean_string(item.get("label")) or code
            internal_property.label = self._clean_string(item.get("label"))
            internal_property.description = self._clean_string(item.get("description"))
            internal_property.entity = self._clean_string(item.get("entity"))
            internal_property.type = property_type
            internal_property.required = bool(item.get("required"))
            internal_property.editable = bool(item.get("editable"))
            internal_property.accepted_values = accepted_values
            internal_property.regex = self._clean_string(item.get("regex"))
            internal_property.is_condition = bool(condition_code and code == condition_code)
            internal_property.raw_data = item
            internal_property.save()
            self.summary_data["internal_properties"] += 1

            active_option_values: set[str] = set()
            for index, option_payload in enumerate(accepted_values):
                option_value = self._clean_string(option_payload.get("value"))
                if not option_value:
                    continue
                active_option_values.add(option_value)
                option, _ = MiraklInternalPropertyOption.objects.get_or_create(
                    internal_property=internal_property,
                    value=option_value,
                    defaults={
                        "sales_channel": self.sales_channel,
                        "multi_tenant_company": self.sales_channel.multi_tenant_company,
                    },
                )
                option.sales_channel = self.sales_channel
                option.multi_tenant_company = self.sales_channel.multi_tenant_company
                option.label = self._clean_string(option_payload.get("label")) or option_value
                option.description = self._clean_string(option_payload.get("description"))
                option.sort_order = index
                option.is_active = True
                option.save()
                self.summary_data["internal_property_options"] += 1

            MiraklInternalPropertyOption.objects.filter(
                internal_property=internal_property,
            ).exclude(value__in=active_option_values).update(is_active=False)
            self._increment_progress()

    def sync_document_types(self, *, document_types: list[dict[str, Any]]) -> None:
        for item in document_types:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            document_type, _ = MiraklDocumentType.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                remote_id=code,
            )
            document_type.name = self._clean_string(item.get("label")) or code
            document_type.description = self._clean_string(item.get("description"))
            document_type.raw_data = item
            document_type.save()
            self.summary_data["document_types"] += 1
            self._increment_progress()

    def sync_categories(self, *, hierarchies: list[dict[str, Any]]) -> None:
        categories_by_code: dict[str, MiraklCategory] = {}
        parent_codes: set[str] = set()

        for item in hierarchies:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            parent_code = self._clean_string(item.get("parent_code"))
            if parent_code:
                parent_codes.add(parent_code)

            category, _ = MiraklCategory.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                remote_id=code,
            )
            category.name = self._clean_string(item.get("label")) or code
            category.parent_code = parent_code
            category.level = self._to_int(item.get("level"))
            category.raw_data = item
            category.save()
            categories_by_code[code] = category
            self.summary_data["categories"] += 1
            self._increment_progress()

        for code, category in categories_by_code.items():
            parent = categories_by_code.get(category.parent_code) if category.parent_code else None
            category.parent = parent
            category.is_leaf = code not in parent_codes
            category.save(update_fields=["parent", "is_leaf"])

    def sync_properties(self, *, attributes: list[dict[str, Any]]) -> None:
        for item in attributes:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            values_list_code = self._clean_string(item.get("values_list"))
            inline_values = self._parse_value_entries(item.get("values"))
            property_type = self._map_remote_type(
                remote_type=item.get("type"),
                has_values=bool(values_list_code or inline_values),
                type_parameter=item.get("type_parameter"),
                type_parameters=item.get("type_parameters"),
            )

            remote_property, _ = MiraklProperty.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                code=code,
                defaults={
                    "type": property_type,
                },
            )
            remote_property.code = code
            remote_property.name = self._clean_string(item.get("label")) or code
            remote_property.description = self._clean_string(item.get("description"))
            remote_property.type = property_type
            remote_property.required = bool(item.get("required"))
            remote_property.variant = bool(item.get("variant"))
            remote_property.requirement_level = self._clean_string(item.get("requirement_level"))
            remote_property.default_value = self._clean_string(item.get("default_value"))
            remote_property.value_list_code = values_list_code
            remote_property.value_list_label = self._value_list_labels.get(values_list_code, remote_property.value_list_label)
            remote_property.validations = self._ensure_json_value(item.get("validations"), default={})
            remote_property.transformations = self._ensure_json_value(item.get("transformations"), default=[])
            remote_property.raw_data = item
            remote_property.save()
            self.summary_data["properties"] += 1

            if inline_values and not values_list_code:
                self._inline_property_values[remote_property.code] = inline_values

            hierarchy_code = self._clean_string(item.get("hierarchy_code"))
            if hierarchy_code:
                category = MiraklCategory.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=hierarchy_code,
                ).first()
                if category is not None:
                    product_type_item, _ = MiraklProductTypeItem.objects.get_or_create(
                        category=category,
                        property=remote_property,
                        defaults={
                            "sales_channel": self.sales_channel,
                            "multi_tenant_company": self.sales_channel.multi_tenant_company,
                        },
                    )
                    product_type_item.sales_channel = self.sales_channel
                    product_type_item.multi_tenant_company = self.sales_channel.multi_tenant_company
                    product_type_item.required = bool(item.get("required"))
                    product_type_item.variant = bool(item.get("variant"))
                    product_type_item.role_data = self._ensure_json_value(item.get("roles"), default=[])
                    product_type_item.raw_data = item
                    product_type_item.save()
                    self.summary_data["product_type_items"] += 1

            for channel_item in self._normalize_records(item.get("channels")):
                channel_code = self._clean_string(channel_item.get("code"))
                if not channel_code:
                    continue
                view = MiraklSalesChannelView.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=channel_code,
                ).first()
                if view is None:
                    continue
                applicability, _ = MiraklPropertyApplicability.objects.get_or_create(
                    property=remote_property,
                    view=view,
                    defaults={
                        "sales_channel": self.sales_channel,
                        "multi_tenant_company": self.sales_channel.multi_tenant_company,
                    },
                )
                applicability.sales_channel = self.sales_channel
                applicability.multi_tenant_company = self.sales_channel.multi_tenant_company
                applicability.raw_data = channel_item
                applicability.save()
                self.summary_data["property_applicabilities"] += 1

            self._increment_progress()

    def sync_select_values(self, *, value_lists: list[dict[str, Any]]) -> None:
        for value_list in value_lists:
            value_list_code = self._clean_string(value_list.get("code"))
            value_list_label = self._clean_string(value_list.get("label"))
            if not value_list_code:
                continue

            self._value_list_labels[value_list_code] = value_list_label
            matching_properties = list(
                MiraklProperty.objects.filter(
                    sales_channel=self.sales_channel,
                    value_list_code=value_list_code,
                )
            )
            if matching_properties:
                MiraklProperty.objects.filter(
                    id__in=[item.id for item in matching_properties],
                ).update(value_list_label=value_list_label)

            for value_payload in self._parse_value_entries(value_list.get("values")):
                for remote_property in matching_properties:
                    self._upsert_select_value(
                        remote_property=remote_property,
                        value_payload=value_payload,
                        value_list_code=value_list_code,
                        value_list_label=value_list_label,
                    )
                self._increment_progress()

        for property_code, inline_values in self._inline_property_values.items():
            remote_property = MiraklProperty.objects.filter(
                sales_channel=self.sales_channel,
                code=property_code,
            ).first()
            if remote_property is None:
                continue
            for value_payload in inline_values:
                self._upsert_select_value(
                    remote_property=remote_property,
                    value_payload=value_payload,
                    value_list_code="",
                    value_list_label="",
                )
                self._increment_progress()

    def _upsert_select_value(
        self,
        *,
        remote_property: MiraklProperty,
        value_payload: dict[str, Any],
        value_list_code: str,
        value_list_label: str,
    ) -> None:
        code = self._clean_string(value_payload.get("code"))
        label = self._clean_string(value_payload.get("label")) or code
        if not code and not label:
            return

        select_value, _ = MiraklPropertySelectValue.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            remote_property=remote_property,
            remote_id=code or label,
        )
        select_value.code = code
        select_value.value = label
        select_value.translated_value = self._first_translation_text(value_payload.get("label_translations"))
        select_value.value_list_code = value_list_code
        select_value.value_list_label = value_list_label
        select_value.raw_data = value_payload
        select_value.save()
        self.summary_data["property_select_values"] += 1

    def _resolve_condition_code(self, *, additional_fields: list[dict[str, Any]]) -> str:
        exact_candidates: list[str] = []
        fuzzy_candidates: list[str] = []

        for item in additional_fields:
            code = self._clean_string(item.get("code"))
            label = self._clean_string(item.get("label"))
            combined = " ".join(
                filter(
                    None,
                    [
                        self._normalize_lookup_token(code),
                        self._normalize_lookup_token(label),
                    ],
                )
            )
            if not code:
                continue
            if self._normalize_lookup_token(code) == "condition":
                exact_candidates.append(code)
            elif self._normalize_lookup_token(label) == "condition":
                exact_candidates.append(code)
            elif "condition" in combined:
                fuzzy_candidates.append(code)

        if exact_candidates:
            return exact_candidates[0]
        if fuzzy_candidates:
            return fuzzy_candidates[0]
        return ""

    def _map_remote_type(
        self,
        *,
        remote_type: Any,
        has_values: bool = False,
        type_parameter: Any = None,
        type_parameters: Any = None,
    ) -> str:
        normalized = self._normalize_lookup_token(remote_type)
        normalized_parameter = self._normalize_lookup_token(type_parameter)
        normalized_parameters = json.dumps(self._ensure_json_value(type_parameters, default=[])).lower()

        if has_values:
            if "multi" in normalized or "multi" in normalized_parameter or "multi" in normalized_parameters:
                return Property.TYPES.MULTISELECT
            return Property.TYPES.SELECT

        if normalized in {"boolean", "yes_no", "yesno"}:
            return Property.TYPES.BOOLEAN
        if normalized in {"integer", "int", "long"}:
            return Property.TYPES.INT
        if normalized in {"decimal", "float", "number"}:
            return Property.TYPES.FLOAT
        if normalized in {"date"}:
            return Property.TYPES.DATE
        if normalized in {"datetime", "timestamp"}:
            return Property.TYPES.DATETIME
        if normalized in {"rich_text", "html", "textarea", "description"}:
            return Property.TYPES.DESCRIPTION
        return Property.TYPES.TEXT

    def _parse_accepted_values(self, raw_value: Any) -> list[dict[str, str]]:
        if raw_value in (None, "", []):
            return []

        parsed_value = raw_value
        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if not stripped:
                return []
            try:
                parsed_value = json.loads(stripped)
            except (TypeError, ValueError):
                split_values = [
                    part.strip()
                    for part in re.split(r"[\n\r,;|]+", stripped)
                    if part and part.strip()
                ]
                parsed_value = split_values

        options: list[dict[str, str]] = []
        for entry in self._normalize_records(parsed_value):
            normalized = self._normalize_option_entry(entry)
            if normalized is not None:
                options.append(normalized)

        if options:
            return self._dedupe_option_entries(options=options)

        if isinstance(parsed_value, list):
            scalar_options = []
            for entry in parsed_value:
                normalized = self._normalize_option_entry(entry)
                if normalized is not None:
                    scalar_options.append(normalized)
            return self._dedupe_option_entries(options=scalar_options)

        return []

    def _parse_value_entries(self, raw_value: Any) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        if isinstance(raw_value, dict):
            raw_items = [raw_value]
        elif isinstance(raw_value, list):
            raw_items = raw_value
        else:
            raw_items = []

        for entry in raw_items:
            normalized = self._normalize_option_entry(entry)
            if normalized is None:
                continue
            if not normalized.get("label"):
                normalized["label"] = normalized.get("value", "")
            entries.append(
                {
                    "code": normalized.get("value", ""),
                    "label": normalized.get("label", ""),
                    "description": normalized.get("description", ""),
                }
            )
        return self._dedupe_option_entries(options=entries)

    def _normalize_option_entry(self, entry: Any) -> dict[str, str] | None:
        if isinstance(entry, dict):
            value = self._clean_string(
                entry.get("code") or entry.get("value") or entry.get("id") or entry.get("key")
            )
            label = self._clean_string(
                entry.get("label") or entry.get("name") or entry.get("value") or entry.get("code")
            )
            description = self._clean_string(entry.get("description"))
        else:
            value = self._clean_string(entry)
            label = value
            description = ""

        if not value and not label:
            return None

        return {
            "value": value or label,
            "label": label or value,
            "description": description,
        }

    def _dedupe_option_entries(self, *, options: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        deduped: list[dict[str, str]] = []
        for option in options:
            key = self._clean_string(option.get("value")) or self._clean_string(option.get("label"))
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(option)
        return deduped

    def _normalize_records(self, raw_value: Any) -> list[dict[str, Any]]:
        if isinstance(raw_value, list):
            return [entry for entry in raw_value if isinstance(entry, dict)]
        if isinstance(raw_value, dict):
            return [raw_value]
        return []

    def _ensure_json_value(self, raw_value: Any, *, default: Any) -> Any:
        if raw_value in (None, ""):
            return default
        if isinstance(raw_value, (dict, list, bool, int, float)):
            return raw_value
        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if not stripped:
                return default
            try:
                return json.loads(stripped)
            except (TypeError, ValueError):
                return raw_value
        return raw_value

    def _first_translation_text(self, raw_value: Any) -> str:
        if isinstance(raw_value, dict):
            for value in raw_value.values():
                cleaned = self._clean_string(value)
                if cleaned:
                    return cleaned
            return ""

        if isinstance(raw_value, list):
            for item in raw_value:
                if isinstance(item, dict):
                    for key in ("label", "value", "name", "description", "text"):
                        cleaned = self._clean_string(item.get(key))
                        if cleaned:
                            return cleaned
                else:
                    cleaned = self._clean_string(item)
                    if cleaned:
                        return cleaned
        return ""

    @staticmethod
    def _clean_string(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _normalize_lookup_token(value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
