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
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklPropertySelectValue,
    MiraklPublicDefinition,
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
        self._value_list_single_defaults: dict[str, str] = {}
        self.summary_data = {
            "categories": 0,
            "document_types": 0,
            "properties": 0,
            "product_type_items": 0,
            "property_applicabilities": 0,
            "property_select_values": 0,
        }
        self._progress_total = 0
        self._progress_processed = 0

    def run(self) -> dict[str, int]:
        document_types = self._get_document_types()
        hierarchies = self._get_hierarchies()
        attributes = self._get_attributes()
        value_lists = self._get_value_lists()

        self._prepare_progress(
            document_types=document_types,
            hierarchies=hierarchies,
            attributes=attributes,
            value_lists=value_lists,
        )
        self._index_value_lists(value_lists=value_lists)

        self.sync_document_types(document_types=document_types)
        self.sync_categories(hierarchies=hierarchies)
        self.sync_properties(attributes=attributes)
        self.sync_select_values(value_lists=value_lists)
        return self.summary_data

    def _get_document_types(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/documents")
        return self._normalize_records(response.get("document_types"))

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
            len(document_types) + len(hierarchies) + len(attributes) + value_count,
        )

        if self.import_process is None:
            return

        self.import_process.total_records = self._progress_total
        self.import_process.processed_records = 0
        self.import_process.percentage = 0
        self.import_process.save(update_fields=["total_records", "processed_records", "percentage"])

    def _index_value_lists(self, *, value_lists: list[dict[str, Any]]) -> None:
        for value_list in value_lists:
            value_list_code = self._clean_string(value_list.get("code"))
            if not value_list_code:
                continue
            self._value_list_labels[value_list_code] = self._clean_string(value_list.get("label"))
            parsed_values = self._parse_value_entries(value_list.get("values"))
            if len(parsed_values) == 1:
                self._value_list_single_defaults[value_list_code] = self._clean_string(parsed_values[0].get("code"))

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

    def sync_categories(self, *, hierarchies: list[dict[str, Any]]) -> None:
        categories_by_code: dict[str, MiraklCategory] = {}
        product_types_by_code: dict[str, MiraklProductType] = {}
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

            product_type, _ = MiraklProductType.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                remote_id=code,
            )
            product_type.category = category
            product_type.name = category.name
            product_type.imported = True
            product_type.save()
            product_types_by_code[code] = product_type
            self.summary_data["categories"] += 1
            self._increment_progress()

        for code, category in categories_by_code.items():
            parent = categories_by_code.get(category.parent_code) if category.parent_code else None
            category.parent = parent
            category.is_leaf = code not in parent_codes
            category.save(update_fields=["parent", "is_leaf"])

            product_type = product_types_by_code.get(code)
            if product_type is not None:
                update_fields: list[str] = []
                if product_type.category_id != category.id:
                    product_type.category = category
                    update_fields.append("category")
                if product_type.name != category.name:
                    product_type.name = category.name
                    update_fields.append("name")
                if update_fields:
                    product_type.save(update_fields=update_fields)

    def sync_document_types(self, *, document_types: list[dict[str, Any]]) -> None:
        for item in document_types:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            remote_document_type = self._get_existing_by_lookup(
                model_class=MiraklDocumentType,
                lookup={
                    "sales_channel": self.sales_channel,
                    "multi_tenant_company": self.sales_channel.multi_tenant_company,
                    "remote_id": code,
                },
            )
            if remote_document_type is None:
                remote_document_type = MiraklDocumentType(
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    remote_id=code,
                )

            remote_document_type.name = self._clean_string(item.get("label")) or code
            remote_document_type.description = self._clean_string(item.get("description"))
            remote_document_type.entity = self._clean_string(item.get("entity"))
            remote_document_type.mime_types = self._ensure_json_value(item.get("mime_types"), default=[])
            remote_document_type.raw_data = item
            remote_document_type.save()

            self.summary_data["document_types"] += 1
            self._increment_progress()

    def sync_properties(self, *, attributes: list[dict[str, Any]]) -> None:
        for item in attributes:
            code = self._clean_string(item.get("code"))
            if not code:
                continue

            values_list_code = self._resolve_value_list_code(item=item)
            inline_values = self._parse_value_entries(item.get("values"))
            property_type = self._map_remote_type(
                remote_type=item.get("type"),
                has_values=bool(values_list_code or inline_values),
                type_parameter=item.get("type_parameter"),
                type_parameters=item.get("type_parameters"),
            )

            remote_property = self._get_existing_by_lookup(
                model_class=MiraklProperty,
                lookup={
                    "sales_channel": self.sales_channel,
                    "multi_tenant_company": self.sales_channel.multi_tenant_company,
                    "code": code,
                },
            )
            if remote_property is None:
                remote_property = MiraklProperty(
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    code=code,
                )
            remote_property.code = code
            remote_property.name = self._clean_string(item.get("label")) or code
            remote_property.description = self._clean_string(item.get("description"))
            remote_property.example = self._clean_string(item.get("example"))
            remote_property.hierarchy_code = self._clean_string(item.get("hierarchy_code"))
            remote_property.is_common = not bool(remote_property.hierarchy_code)
            remote_property.unique_code = self._clean_string(item.get("unique_code"))
            remote_property.type = property_type
            remote_property.representation_type = self._detect_representation_type(
                item=item,
                values_list_code=values_list_code,
                inline_values=inline_values,
            )
            remote_property.required = bool(item.get("required"))
            remote_property.variant = bool(item.get("variant"))
            remote_property.requirement_level = self._clean_string(item.get("requirement_level"))
            remote_property.default_value = self._detect_default_value(
                item=item,
                values_list_code=values_list_code,
                inline_values=inline_values,
                representation_type=remote_property.representation_type,
            )
            remote_property.value_list_code = values_list_code
            remote_property.value_list_label = self._value_list_labels.get(values_list_code, remote_property.value_list_label)
            remote_property.description_translations = self._ensure_json_value(item.get("description_translations"), default=[])
            remote_property.label_translations = self._ensure_json_value(item.get("label_translations"), default=[])
            remote_property.type_parameters = self._ensure_json_value(item.get("type_parameters"), default=[])
            remote_property.validations = self._ensure_json_value(item.get("validations"), default={})
            remote_property.transformations = self._ensure_json_value(item.get("transformations"), default=[])
            remote_property.raw_data = item
            self._apply_public_definition(remote_property=remote_property)
            remote_property.save()
            self.summary_data["properties"] += 1

            if inline_values and not values_list_code:
                self._inline_property_values[remote_property.code] = inline_values

            hierarchy_code = self._clean_string(item.get("hierarchy_code"))
            if hierarchy_code:
                product_type = MiraklProductType.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=hierarchy_code,
                ).first()
                if product_type is not None:
                    product_type_item, _ = MiraklProductTypeItem.objects.get_or_create(
                        sales_channel=self.sales_channel,
                        multi_tenant_company=self.sales_channel.multi_tenant_company,
                        product_type=product_type,
                        remote_property=remote_property,
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
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    property=remote_property,
                    view=view,
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

    def _get_existing_by_lookup(self, *, model_class, lookup: dict[str, Any]):
        return model_class.objects.filter(**lookup).order_by("id").first()

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
        translations = self._ensure_json_value(value_payload.get("label_translations"), default=[])
        select_value.label_translations = translations
        select_value.value_label_translations = translations
        select_value.value_list_code = value_list_code
        select_value.value_list_label = value_list_label
        select_value.raw_data = value_payload
        select_value.save()
        self.summary_data["property_select_values"] += 1

    def _resolve_value_list_code(self, *, item: dict[str, Any]) -> str:
        direct_value = self._clean_string(item.get("values_list"))
        if direct_value:
            return direct_value

        for type_parameter in self._ensure_json_value(item.get("type_parameters"), default=[]):
            if not isinstance(type_parameter, dict):
                continue
            if self._normalize_lookup_token(type_parameter.get("name")) != "list_code":
                continue
            resolved_value = self._clean_string(type_parameter.get("value"))
            if resolved_value:
                return resolved_value

        return ""

    def _detect_representation_type(
        self,
        *,
        item: dict[str, Any],
        values_list_code: str,
        inline_values: list[dict[str, Any]],
    ) -> str:
        code = self._normalize_lookup_token(item.get("code"))
        label = self._normalize_lookup_token(item.get("label"))
        field_type = self._normalize_lookup_token(item.get("type"))
        type_parameters = self._ensure_json_value(item.get("type_parameters"), default=[])
        media_type = self._resolve_media_type(type_parameters=type_parameters)

        if field_type in {"list", "list_multiple_values"}:
            value_count = len(inline_values) or (1 if values_list_code in self._value_list_single_defaults else 0)
            if value_count == 1:
                return MiraklProperty.REPRESENTATION_DEFAULT_VALUE

        if code.endswith("_uom") or label.endswith(" unit"):
            return MiraklProperty.REPRESENTATION_UNIT
        if any(token in code for token in {"product_title", "product_name"}) or code == "name":
            return MiraklProperty.REPRESENTATION_PRODUCT_TITLE
        if "subtitle" in code:
            return MiraklProperty.REPRESENTATION_PRODUCT_SUBTITLE
        if "short_description" in code:
            return MiraklProperty.REPRESENTATION_PRODUCT_SHORT_DESCRIPTION
        if "bullet" in code:
            return MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT
        if code in {"product_category", "category"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CATEGORY
        if code in {"sku", "product_sku", "shop_sku"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_SKU
        if code in {"parent_product_id", "variant_group_code", "configurable_id"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_ID
        if code in {"parent_sku", "configurable_sku"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU
        if "url_key" in code:
            return MiraklProperty.REPRESENTATION_PRODUCT_URL_KEY
        if code == "ean" or code.endswith("_ean") or "ean_code" in code:
            return MiraklProperty.REPRESENTATION_PRODUCT_EAN
        if code in {"main_image", "thumbnail_image"}:
            return MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE
        if code == "swatch":
            return MiraklProperty.REPRESENTATION_SWATCH_IMAGE
        if field_type == "media" and media_type == "document":
            return MiraklProperty.REPRESENTATION_DOCUMENT
        if field_type == "media" and media_type == "image":
            return MiraklProperty.REPRESENTATION_IMAGE
        if "image" in code:
            return MiraklProperty.REPRESENTATION_IMAGE
        if "video" in code:
            return MiraklProperty.REPRESENTATION_VIDEO
        if "vat" in code or "tax_rate" in code:
            return MiraklProperty.REPRESENTATION_VAT_RATE
        if "backorder" in code:
            return MiraklProperty.REPRESENTATION_ALLOW_BACKORDER
        if code in {"long_description", "description"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_DESCRIPTION
        if code == "active":
            return MiraklProperty.REPRESENTATION_PRODUCT_ACTIVE
        return MiraklProperty.REPRESENTATION_PROPERTY

    def _detect_default_value(
        self,
        *,
        item: dict[str, Any],
        values_list_code: str,
        inline_values: list[dict[str, Any]],
        representation_type: str,
    ) -> str:
        explicit_default = self._clean_string(item.get("default_value"))
        if explicit_default:
            return explicit_default
        if representation_type != MiraklProperty.REPRESENTATION_DEFAULT_VALUE:
            return ""
        if len(inline_values) == 1:
            return self._clean_string(inline_values[0].get("code"))
        return self._value_list_single_defaults.get(values_list_code, "")

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
        has_multi_values = (
            normalized == "list_multiple_values"
            or "multi" in normalized
            or "multi" in normalized_parameter
            or "multi" in normalized_parameters
        )

        if normalized in {"list", "list_multiple_values"} or has_values:
            if has_multi_values:
                return Property.TYPES.MULTISELECT
            return Property.TYPES.SELECT

        if normalized in {"boolean", "yes_no", "yesno"}:
            return Property.TYPES.BOOLEAN
        if normalized in {"integer", "int", "long"}:
            return Property.TYPES.INT
        if normalized in {"decimal", "float", "number", "numeric"}:
            return Property.TYPES.FLOAT
        if normalized in {"date"}:
            return Property.TYPES.DATE
        if normalized in {"datetime", "timestamp"}:
            return Property.TYPES.DATETIME
        if normalized in {"long_text", "rich_text", "html", "textarea", "description"}:
            return Property.TYPES.DESCRIPTION
        if normalized in {"media", "link", "regex", "string"}:
            return Property.TYPES.TEXT
        return Property.TYPES.TEXT

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

    def _resolve_media_type(self, *, type_parameters: Any) -> str:
        for item in self._ensure_json_value(type_parameters, default=[]):
            if not isinstance(item, dict):
                continue
            if self._normalize_lookup_token(item.get("name")) != "type":
                continue
            resolved = self._normalize_lookup_token(item.get("value"))
            if resolved:
                return resolved
        return ""

    def _apply_public_definition(self, *, remote_property: MiraklProperty) -> None:
        public_definition = (
            MiraklPublicDefinition.objects.filter(
                hostname=self.sales_channel.hostname,
                property_code=remote_property.code,
            )
            .order_by("id")
            .first()
        )
        if public_definition is None:
            return

        remote_property.representation_type = public_definition.representation_type
        remote_property.default_value = public_definition.default_value or remote_property.default_value
        remote_property.yes_text_value = public_definition.yes_text_value or remote_property.yes_text_value
        remote_property.no_text_value = public_definition.no_text_value or remote_property.no_text_value
        remote_property.representation_type_decided = True
