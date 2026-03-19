from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

from properties.models import Property

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.utils.type_parameters import (
    get_mirakl_type_parameter_value,
    normalize_mirakl_type_parameters,
)
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
        self._hierarchy_levels: dict[str, int] = {}
        self._all_hierarchy_codes: list[str] = []
        self._descendant_hierarchy_codes: dict[str, list[str]] = {}
        self._inline_property_values: dict[str, list[dict[str, Any]]] = {}
        self._value_list_labels: dict[str, str] = {}
        self._value_list_single_defaults: dict[str, str] = {}
        self._offer_states_value_list_code = "offer_states"
        self._offer_states_value_list_label = "Offer states"
        self._offer_state_property_code = "offer_state"
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
        offer_states = self._get_offer_states()
        hierarchies = self._get_hierarchies()
        self._hierarchy_levels = {
            self._clean_string(item.get("code")): self._to_int(item.get("level"))
            for item in hierarchies
            if self._clean_string(item.get("code"))
        }
        self._all_hierarchy_codes = list(self._hierarchy_levels.keys())
        self._descendant_hierarchy_codes = self._build_descendant_hierarchy_codes(hierarchies=hierarchies)
        value_lists = self._get_value_lists()
        attributes = self._get_attributes()

        self._prepare_progress(
            document_types=document_types,
            offer_states=offer_states,
            hierarchies=hierarchies,
            attributes=attributes,
            value_lists=value_lists,
        )
        self._index_value_lists(value_lists=value_lists)

        self.sync_document_types(document_types=document_types)
        self.sync_categories(hierarchies=hierarchies)
        self.sync_properties(attributes=attributes)
        self.sync_select_values(value_lists=value_lists)
        self.sync_offer_state_property(offer_states=offer_states)
        self.sync_default_value_labels()
        return self.summary_data

    def _get_document_types(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(path="/api/documents")
        return self._normalize_records(response.get("document_types"))

    def _get_offer_states(self) -> list[dict[str, Any]]:
        response = self.mirakl_get(
            path="/api/offers/states",
            params={"active": "true"},
        )
        return self._normalize_records(response.get("offer_states"))

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
        offer_states: list[dict[str, Any]],
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
        value_count += len(offer_states)

        self._progress_total = max(
            1,
            len(document_types) + len(hierarchies) + len(attributes) + 1 + value_count,
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
        product_types_by_code = {
            product_type.remote_id: product_type
            for product_type in MiraklProductType.objects.filter(sales_channel=self.sales_channel)
        }
        expected_property_ids_by_product_type: dict[int, set[int]] = {
            product_type.id: set()
            for product_type in product_types_by_code.values()
        }

        for item in self._sort_attributes_for_import(attributes=attributes):
            remote_property = self._upsert_property(item=item)
            if remote_property is None:
                continue

            self._sync_property_applicabilities(remote_property=remote_property, item=item)
            for product_type in self._resolve_target_product_types(
                item=item,
                product_types_by_code=product_types_by_code,
            ):
                expected_property_ids_by_product_type.setdefault(product_type.id, set()).add(remote_property.id)
                self._upsert_product_type_item(
                    product_type=product_type,
                    remote_property=remote_property,
                    item=item,
                )
            self._increment_progress()

        for product_type in product_types_by_code.values():
            expected_property_ids = expected_property_ids_by_product_type.get(product_type.id, set())
            stale_items = MiraklProductTypeItem.objects.filter(product_type=product_type)
            if expected_property_ids:
                stale_items = stale_items.exclude(remote_property_id__in=expected_property_ids)
            stale_items.delete()

    def _upsert_property(self, *, item: dict[str, Any]) -> MiraklProperty | None:
        code = self._clean_string(item.get("code"))
        if not code:
            return None

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
        if self._should_replace_property_definition(remote_property=remote_property, item=item):
            remote_property.code = code
            remote_property.name = self._build_property_name(item=item, code=code)
            remote_property.description = self._clean_string(item.get("description"))
            remote_property.example = self._clean_string(item.get("example"))
            remote_property.is_common = not bool(self._clean_string(item.get("hierarchy_code")))
            remote_property.type = property_type
            remote_property.allows_unmapped_values = property_type not in {
                Property.TYPES.SELECT,
                Property.TYPES.MULTISELECT,
            }
            remote_property.representation_type = self._detect_representation_type(
                item=item,
                values_list_code=values_list_code,
                inline_values=inline_values,
            )
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

        return remote_property

    def _build_property_name(self, *, item: dict[str, Any], code: str) -> str:
        base_name = self._clean_string(item.get("label")) or code
        unit = self._resolve_type_parameter_value(
            type_parameters=item.get("type_parameters"),
            name="UNIT",
        )
        if not unit:
            return base_name
        suffix = f" ({unit})"
        if base_name.endswith(suffix):
            return base_name
        return f"{base_name}{suffix}"

    def _upsert_product_type_item(self, *, product_type: MiraklProductType, remote_property: MiraklProperty, item: dict[str, Any]) -> None:
        product_type_item, _ = MiraklProductTypeItem.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            product_type=product_type,
            remote_property=remote_property,
        )
        if product_type_item.pk and product_type_item.hierarchy_code:
            existing_score = self._attribute_specificity_score(
                hierarchy_code=product_type.remote_id,
                item={"hierarchy_code": product_type_item.hierarchy_code},
            )
            incoming_score = self._attribute_specificity_score(
                hierarchy_code=product_type.remote_id,
                item=item,
            )
            if existing_score > incoming_score:
                return
        product_type_item.sales_channel = self.sales_channel
        product_type_item.multi_tenant_company = self.sales_channel.multi_tenant_company
        product_type_item.hierarchy_code = self._clean_string(item.get("hierarchy_code"))
        product_type_item.required = bool(item.get("required"))
        product_type_item.variant = bool(item.get("variant"))
        product_type_item.requirement_level = self._clean_string(item.get("requirement_level"))
        product_type_item.role_data = self._ensure_json_value(item.get("roles"), default=[])
        product_type_item.raw_data = item
        product_type_item.save()
        self.summary_data["product_type_items"] += 1

    def _sync_property_applicabilities(self, *, remote_property: MiraklProperty, item: dict[str, Any]) -> None:
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

    def sync_offer_state_property(self, *, offer_states: list[dict[str, Any]]) -> None:
        if not offer_states:
            return

        remote_property = self._get_existing_by_lookup(
            model_class=MiraklProperty,
            lookup={
                "sales_channel": self.sales_channel,
                "multi_tenant_company": self.sales_channel.multi_tenant_company,
                "code": self._offer_state_property_code,
            },
        )
        if remote_property is None:
            remote_property = MiraklProperty(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                code=self._offer_state_property_code,
            )

        remote_property.code = self._offer_state_property_code
        remote_property.name = "Condition"
        remote_property.description = "Offer state / condition values imported from OF61."
        remote_property.example = ""
        remote_property.is_common = False
        remote_property.type = Property.TYPES.SELECT
        remote_property.allows_unmapped_values = False
        remote_property.representation_type = MiraklProperty.REPRESENTATION_CONDITION
        remote_property.value_list_code = self._offer_states_value_list_code
        remote_property.value_list_label = self._offer_states_value_list_label
        remote_property.save()
        self.summary_data["properties"] += 1

        for offer_state in offer_states:
            self._upsert_select_value(
                remote_property=remote_property,
                value_payload=offer_state,
                value_list_code=self._offer_states_value_list_code,
                value_list_label=self._offer_states_value_list_label,
            )
            self._increment_progress()

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

    def sync_default_value_labels(self) -> None:
        queryset = MiraklProperty.objects.filter(
            sales_channel=self.sales_channel,
            representation_type=MiraklProperty.REPRESENTATION_DEFAULT_VALUE,
        ).order_by("id")

        for remote_property in queryset.iterator():
            select_values = list(
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                )
                .order_by("id")[:2]
            )
            resolved_default = self._resolve_default_value_label(
                remote_property=remote_property,
                select_values=select_values,
            )
            if resolved_default == remote_property.default_value:
                continue
            remote_property.default_value = resolved_default
            remote_property.save(update_fields=["default_value"])

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

        return self._resolve_type_parameter_value(
            type_parameters=item.get("type_parameters"),
            name="LIST_CODE",
        )

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

        if code.endswith("_uom") or label.endswith(" unit"):
            return MiraklProperty.REPRESENTATION_UNIT
        if field_type in {"list", "list_multiple_values"}:
            value_count = len(inline_values) or (1 if values_list_code in self._value_list_single_defaults else 0)
            if value_count == 1:
                return MiraklProperty.REPRESENTATION_DEFAULT_VALUE
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
        if code in {"sku", "product_sku", "shop_sku", "product_id"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_SKU
        if code in {"parent_product_id", "parent_sku", "configurable_sku"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_SKU
        if code in {"variant_group_code", "configurable_id"}:
            return MiraklProperty.REPRESENTATION_PRODUCT_CONFIGURABLE_ID
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
        if code in {"long_description", "description", "details_and_care"} or code.startswith("long_description_") or code.startswith("details_and_care_"):
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
        type_parameter_default = self._resolve_type_parameter_value(
            type_parameters=item.get("type_parameters"),
            name="DEFAULT_VALUE",
        )
        if type_parameter_default:
            return type_parameter_default
        if representation_type != MiraklProperty.REPRESENTATION_DEFAULT_VALUE:
            return ""
        if len(inline_values) == 1:
            return self._clean_string(inline_values[0].get("code"))
        return self._value_list_single_defaults.get(values_list_code, "")

    def _resolve_default_value_label(
        self,
        *,
        remote_property: MiraklProperty,
        select_values: list[MiraklPropertySelectValue] | None = None,
    ) -> str:
        if select_values is None:
            select_values = list(
                MiraklPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_property=remote_property,
                ).order_by("id")
            )

        raw_default = self._clean_string(remote_property.default_value)
        if len(select_values) == 1:
            select_value = select_values[0]
            return self._clean_string(select_value.value) or self._clean_string(select_value.code) or raw_default

        if not raw_default:
            return ""

        for select_value in select_values:
            if raw_default in {
                self._clean_string(select_value.code),
                self._clean_string(select_value.remote_id),
                self._clean_string(select_value.value),
            }:
                return self._clean_string(select_value.value) or self._clean_string(select_value.code) or raw_default

        return raw_default

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
        return self._normalize_lookup_token(
            get_mirakl_type_parameter_value(
                raw_value=type_parameters,
                name="TYPE",
            )
        )

    def _resolve_type_parameter_value(self, *, type_parameters: Any, name: str) -> str:
        return self._clean_string(
            get_mirakl_type_parameter_value(
                raw_value=normalize_mirakl_type_parameters(raw_value=type_parameters),
                name=name,
            )
        )

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

    def _build_descendant_hierarchy_codes(self, *, hierarchies: list[dict[str, Any]]) -> dict[str, list[str]]:
        children_by_parent: dict[str, list[str]] = {}
        for hierarchy in hierarchies:
            code = self._clean_string(hierarchy.get("code"))
            if not code:
                continue
            parent_code = self._clean_string(hierarchy.get("parent_code"))
            if parent_code:
                children_by_parent.setdefault(parent_code, []).append(code)

        descendants_by_code: dict[str, list[str]] = {}

        def collect(code: str) -> list[str]:
            if code in descendants_by_code:
                return descendants_by_code[code]
            descendants = [code]
            for child_code in children_by_parent.get(code, []):
                descendants.extend(collect(child_code))
            descendants_by_code[code] = descendants
            return descendants

        for hierarchy_code in self._all_hierarchy_codes:
            collect(hierarchy_code)

        return descendants_by_code

    def _sort_attributes_for_import(self, *, attributes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            attributes,
            key=lambda item: self._attribute_item_specificity_score(item=item),
            reverse=True,
        )

    def _attribute_item_specificity_score(self, *, item: dict[str, Any]) -> tuple[int, int]:
        hierarchy_code = self._clean_string(item.get("hierarchy_code"))
        if hierarchy_code:
            return (1, self._category_level(hierarchy_code))
        return (0, -1)

    def _should_replace_property_definition(self, *, remote_property: MiraklProperty, item: dict[str, Any]) -> bool:
        if remote_property.pk is None:
            return True
        existing_raw_data = remote_property.raw_data or {}
        existing_score = self._attribute_item_specificity_score(item=existing_raw_data)
        incoming_score = self._attribute_item_specificity_score(item=item)
        return incoming_score >= existing_score

    def _resolve_target_product_types(
        self,
        *,
        item: dict[str, Any],
        product_types_by_code: dict[str, MiraklProductType],
    ) -> list[MiraklProductType]:
        hierarchy_code = self._clean_string(item.get("hierarchy_code"))
        if not hierarchy_code:
            target_codes = self._all_hierarchy_codes
        else:
            target_codes = self._descendant_hierarchy_codes.get(hierarchy_code, [hierarchy_code])
        return [
            product_types_by_code[target_code]
            for target_code in target_codes
            if target_code in product_types_by_code
        ]

    def _dedupe_attributes_for_hierarchy(self, *, hierarchy_code: str, attributes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped_by_code: dict[str, dict[str, Any]] = {}
        for item in attributes:
            code = self._clean_string(item.get("code"))
            if not code:
                continue
            previous = deduped_by_code.get(code)
            if previous is None:
                deduped_by_code[code] = item
                continue
            if self._attribute_specificity_score(hierarchy_code=hierarchy_code, item=item) >= self._attribute_specificity_score(
                hierarchy_code=hierarchy_code,
                item=previous,
            ):
                deduped_by_code[code] = item
        return list(deduped_by_code.values())

    def _attribute_specificity_score(self, *, hierarchy_code: str, item: dict[str, Any]) -> tuple[int, int]:
        item_hierarchy_code = self._clean_string(item.get("hierarchy_code"))
        if item_hierarchy_code == hierarchy_code:
            return (2, self._category_level(item_hierarchy_code))
        if item_hierarchy_code:
            return (1, self._category_level(item_hierarchy_code))
        return (0, -1)

    def _category_level(self, hierarchy_code: str) -> int:
        return self._hierarchy_levels.get(hierarchy_code, 0)
