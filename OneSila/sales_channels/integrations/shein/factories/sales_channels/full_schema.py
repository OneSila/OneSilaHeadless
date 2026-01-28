"""Factories to mirror Shein category trees and product types locally."""

import logging
import math
from typing import Any, Optional
from urllib.parse import urlparse
from core.helpers import get_languages

from sales_channels.integrations.shein import constants
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinRemoteLanguage,
    SheinSalesChannel,
)


logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGE_CODES = {code.lower(): code for code, _ in get_languages()}


PUBLISH_FIELD_FLAG_MAP = {
    "reference_product_link": "reference_product_link_required",
    "proof_of_stock": "proof_of_stock_required",
    "shelf_require": "shelf_require_required",
    "brand_code": "brand_code_required",
    "skc_title": "skc_title_required",
    "minimum_stock_quantity": "minimum_stock_quantity_required",
    "product_detail_picture": "product_detail_picture_required",
    "quantity_info": "quantity_info_required",
    "sample_spec": "sample_spec_required",
}

PUBLISH_MODULE_FLAG_MAP = {
    "reference_info": "reference_info_required",
}


class SheinCategoryTreeSyncFactory(SheinSignatureMixin):
    """Fetch and persist the full category tree for a Shein storefront."""

    category_tree_path = "/open-api/goods/query-category-tree"
    publish_standard_path = "/open-api/goods/query-publish-fill-in-standard"
    attribute_template_path = "/open-api/goods/query-attribute-template"
    custom_attribute_permission_path = "/open-api/goods/get-custom-attribute-permission-config"

    def __init__(
        self,
        *,
        sales_channel: SheinSalesChannel,
        language: Optional[str] = None,
        import_process=None,
        sync_product_type_attributes: bool = True,
    ) -> None:
        self.sales_channel = sales_channel
        self.sales_channel_id = getattr(sales_channel, "pk", None)
        self.language = language
        self.sync_product_type_attributes = sync_product_type_attributes
        self.synced_categories: list[SheinCategory] = []
        self.synced_product_types: list[SheinProductType] = []
        self._remote_language_cache: set[tuple[Optional[int], str]] = set()
        self._attribute_template_cache: dict[str, list[dict[str, Any]]] = {}
        self._custom_value_permission_cache: dict[str, dict[str, bool]] = {}
        self.import_process = import_process
        self._import_total_nodes = 0
        self._import_processed_nodes = 0
        self._import_last_percentage = 0

    def _print_debug(self, message: str) -> None:
        return

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, *, tree: Optional[list[dict[str, Any]]] = None) -> list[SheinCategory]:
        """Fetch the remote tree (when not provided) and persist all nodes."""

        logger.info(
            "Shein schema sync starting for channel=%s language=%s",
            self.sales_channel_id,
            self.language or "auto",
        )
        self._print_debug(
            f"Starting schema sync (language={self.language or 'auto'})",
        )
        nodes = tree if tree is not None else self.fetch_remote_category_tree()
        normalized_nodes = [node for node in nodes if isinstance(node, dict)]
        self.synced_categories = []
        self.synced_product_types = []

        if not normalized_nodes:
            logger.info(
                "Shein schema sync aborted for channel=%s: no nodes returned",
                self.sales_channel_id,
            )
            self._print_debug("No nodes returned from remote tree; aborting run.")
            return []

        logger.info(
            "Shein schema sync will process %s nodes for channel=%s",
            len(normalized_nodes),
            self.sales_channel_id,
        )
        self._print_debug(f"Processing {len(normalized_nodes)} nodes from remote tree.")
        self._prepare_import_progress(nodes=normalized_nodes)

        for node in normalized_nodes:
            self._sync_node(node=node, parent=None)

        logger.info(
            "Shein schema sync finished for channel=%s: %s categories, %s product types",
            self.sales_channel_id,
            len(self.synced_categories),
            len(self.synced_product_types),
        )
        self._print_debug(
            f"Finished schema sync: categories={len(self.synced_categories)} product_types={len(self.synced_product_types)}"
        )
        return self.synced_categories

    def fetch_remote_category_tree(self) -> list[dict[str, Any]]:
        """Call Shein and return the raw category tree."""

        payload = self._build_request_payload()
        logger.info(
            "Requesting Shein category tree for channel=%s payload=%s",
            self.sales_channel_id,
            payload,
        )
        self._print_debug(f"Requesting category tree with payload={payload}")

        try:
            response = self.shein_post(path=self.category_tree_path, payload=payload or None)
        except ValueError:
            logger.exception(
                "Failed to retrieve Shein category tree for Shein channel %s",
                self.sales_channel_id,
            )
            return []

        try:
            data = response.json()
        except ValueError:
            logger.exception(
                "Invalid JSON while fetching Shein category tree for Shein channel %s",
                self.sales_channel_id,
            )
            return []

        if not isinstance(data, dict):
            return []

        info = data.get("info")
        if not isinstance(info, dict):
            return []

        records = info.get("data")
        if not isinstance(records, list):
            return []

        normalized = [record for record in records if isinstance(record, dict)]
        logger.info(
            "Fetched %s remote Shein category nodes for channel=%s",
            len(normalized),
            self.sales_channel_id,
        )
        self._print_debug(f"Received {len(normalized)} nodes from category tree response.")
        return normalized

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_import_progress(self, *, nodes: list[dict[str, Any]]) -> None:
        if not self.import_process:
            return

        total = 0
        for node in nodes:
            total += self._count_category_nodes(node=node)

        self._import_total_nodes = total
        self._import_processed_nodes = 0
        self._import_last_percentage = getattr(self.import_process, "percentage", 0) or 0
        self.import_process.total_records = total
        self.import_process.save()

    def _count_category_nodes(self, *, node: dict[str, Any]) -> int:
        total = 0
        if isinstance(node, dict) and self._normalize_identifier(node.get("category_id")):
            total += 1

        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                total += self._count_category_nodes(node=child)
        return total

    def _increment_import_progress(self) -> None:
        if not self.import_process or not self._import_total_nodes:
            return

        self._import_processed_nodes += 1
        new_percentage = math.floor(
            (self._import_processed_nodes / self._import_total_nodes) * 100
        )
        if new_percentage <= self._import_last_percentage:
            return

        self._import_last_percentage = new_percentage
        self.import_process.processed_records = self._import_processed_nodes
        self.import_process.percentage = new_percentage
        self.import_process.save()

    def _sync_node(self, *, node: dict[str, Any], parent: Optional[SheinCategory]) -> None:
        category = self._sync_category(node=node, parent=parent)
        if category is None:
            return

        self._increment_import_progress()

        children = node.get("children")
        if not isinstance(children, list):
            return

        for child in children:
            if isinstance(child, dict):
                self._sync_node(node=child, parent=category)

    def _sync_category(
        self,
        *,
        node: dict[str, Any],
        parent: Optional[SheinCategory],
    ) -> Optional[SheinCategory]:
        remote_id = self._normalize_identifier(node.get("category_id"))
        if remote_id is None:
            logger.debug("Skipping Shein category without category_id: %s", node)
            return None

        defaults = {
            "name": self._safe_string(node.get("category_name")) or "",
            "parent": parent,
            "parent_remote_id": self._normalize_identifier(node.get("parent_category_id")) or "",
            "is_leaf": self._to_bool(node.get("last_category")),
            "product_type_remote_id": self._normalize_identifier(node.get("product_type_id")) or "",
            "raw_data": self._prepare_raw_payload(node=node),
        }

        category, _ = SheinCategory.objects.update_or_create(
            remote_id=remote_id,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            defaults=defaults,
        )

        self.synced_categories.append(category)

        self._enrich_category_publish_specs(category=category)

        product_type = self._sync_product_type(category=category, node=node)
        if product_type is not None:
            self.synced_product_types.append(product_type)
            logger.info(
                "Linked Shein category %s to product type %s (channel=%s)",
                category.remote_id,
                product_type.remote_id,
                self.sales_channel_id,
            )
            self._print_debug(
                f"Category {category.remote_id} linked to product type {product_type.remote_id}."
            )

        return category

    def _sync_product_type(
        self,
        *,
        category: SheinCategory,
        node: dict[str, Any],
    ) -> Optional[SheinProductType]:
        remote_id = self._normalize_identifier(node.get("product_type_id"))
        if remote_id is None:
            return None

        defaults = {
            "name": self._safe_string(node.get("category_name")),
            "raw_data": self._prepare_raw_payload(node=node),
            "imported": True,
            "category_id": category.remote_id or "",
        }

        product_type, _ = SheinProductType.objects.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            defaults=defaults,
        )

        if self.sync_product_type_attributes:
            self._sync_product_type_attributes(product_type=product_type)
        self._sync_category_configurator_properties(
            category=category,
            product_type=product_type,
        )

        return product_type

    def _enrich_category_publish_specs(self, *, category: SheinCategory) -> None:
        info = self._fetch_publish_fill_in_standard(category_id=category.remote_id)
        if not info:
            return

        fill_in_records = self._extract_fill_in_standard_records(value=info.get("fill_in_standard_list"))
        field_flags = {attr: False for attr in PUBLISH_FIELD_FLAG_MAP.values()}
        module_flags = {attr: False for attr in PUBLISH_MODULE_FLAG_MAP.values()}

        for record in fill_in_records:
            required_flag = self._to_bool(record.get("required"))
            module_name = record.get("module")
            field_key = record.get("field_key")

            module_attr = PUBLISH_MODULE_FLAG_MAP.get(module_name)
            if module_attr and required_flag:
                module_flags[module_attr] = True

            field_attr = PUBLISH_FIELD_FLAG_MAP.get(field_key)
            if field_attr is not None:
                field_flags[field_attr] = required_flag

        default_language = self._safe_string(info.get("default_language")) or ""
        currency = self._safe_string(info.get("currency")) or ""
        picture_config = self._normalize_picture_config(info.get("picture_config_list"))
        support_sale_attribute_sort = info.get("support_sale_attribute_sort")
        if support_sale_attribute_sort is not None:
            support_sale_attribute_sort = self._to_bool(support_sale_attribute_sort)

        tags = self._normalize_fill_configuration_tags(value=info.get("fill_configuration_tags"))
        package_type_required = self._field_required(
            records=fill_in_records,
            field_key="package_type",
        ) or ("PACKAGE_TYPE_TO_SKU" in tags)
        supplier_barcode_required = self._field_required(
            records=fill_in_records,
            field_key="supplier_barcode",
        )

        if default_language:
            self._ensure_remote_language(language_code=default_language)

        update_fields: list[str] = []

        for attr, value in {**module_flags, **field_flags}.items():
            if getattr(category, attr) != value:
                setattr(category, attr, value)
                update_fields.append(attr)

        if default_language != category.default_language:
            category.default_language = default_language
            update_fields.append("default_language")

        if currency != category.currency:
            category.currency = currency
            update_fields.append("currency")

        if picture_config != category.picture_config:
            category.picture_config = picture_config
            update_fields.append("picture_config")

        if support_sale_attribute_sort != category.support_sale_attribute_sort:
            category.support_sale_attribute_sort = support_sale_attribute_sort
            update_fields.append("support_sale_attribute_sort")

        if package_type_required != category.package_type_required:
            category.package_type_required = package_type_required
            update_fields.append("package_type_required")

        if supplier_barcode_required != category.supplier_barcode_required:
            category.supplier_barcode_required = supplier_barcode_required
            update_fields.append("supplier_barcode_required")

        raw_data = category.raw_data or {}
        if isinstance(raw_data, dict):
            publish_standard = raw_data.get("publish_standard")
            if not isinstance(publish_standard, dict):
                publish_standard = {}

            normalized_publish_standard = {
                "default_language": default_language or None,
                "currency": currency or None,
                "support_sale_attribute_sort": support_sale_attribute_sort,
                "fill_configuration_tags": tags,
                "fill_in_standard_list": fill_in_records,
                "picture_config_list": picture_config,
                "package_type_required": package_type_required,
                "supplier_barcode_required": supplier_barcode_required,
                "properties": publish_standard.get(
                    "properties",
                    publish_standard.get("configurator_properties", []),
                ),
            }

            if publish_standard != normalized_publish_standard:
                raw_data = {**raw_data, "publish_standard": normalized_publish_standard}
                category.raw_data = raw_data
                update_fields.append("raw_data")

        if update_fields:
            category.save(update_fields=update_fields)

    def _sync_category_configurator_properties(
        self,
        *,
        category: SheinCategory,
        product_type: SheinProductType,
    ) -> None:
        items = (
            SheinProductTypeItem.objects.filter(product_type=product_type)
            .select_related("property")
            .order_by("property__remote_id")
        )

        configurator_properties: list[dict[str, Any]] = []
        for item in items:
            property_obj = getattr(item, "property", None)
            if not property_obj:
                continue

            configurator_properties.append(
                {
                    "product_type_id": product_type.remote_id,
                    "product_type_item_id": item.remote_id,
                    "property_id": property_obj.remote_id,
                    "property_name": property_obj.name,
                    "property_name_en": property_obj.name_en,
                    "property_type": property_obj.type,
                    "value_mode": property_obj.value_mode,
                    "value_limit": property_obj.value_limit,
                    "visibility": item.visibility,
                    "attribute_type": item.attribute_type,
                    "requirement": item.requirement,
                    "is_main_attribute": item.is_main_attribute,
                    "allows_unmapped_values": item.allows_unmapped_values,
                    "remarks": item.remarks,
                    "raw_data": item.raw_data,
                }
            )

        raw_data = category.raw_data or {}
        if not isinstance(raw_data, dict):
            return

        publish_standard = raw_data.get("publish_standard")
        if not isinstance(publish_standard, dict):
            publish_standard = {}

        next_publish_standard = {
            **publish_standard,
            "properties": configurator_properties,
        }
        if publish_standard == next_publish_standard:
            return

        category.raw_data = {**raw_data, "publish_standard": next_publish_standard}
        category.save(update_fields=["raw_data"])

    @staticmethod
    def _extract_fill_in_standard_records(*, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        normalized_records: list[dict[str, Any]] = []
        for record in value:
            if not isinstance(record, dict):
                continue
            normalized_records.append(
                {
                    "module": record.get("module"),
                    "field_key": record.get("field_key"),
                    "required": SheinCategoryTreeSyncFactory._coerce_bool(value=record.get("required")),
                    "show": SheinCategoryTreeSyncFactory._coerce_bool(value=record.get("show")),
                }
            )
        return normalized_records

    @staticmethod
    def _normalize_fill_configuration_tags(*, value: Any) -> list[str]:
        if value is None:
            return []

        tags: list[str] = []
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",")]
            tags = [part for part in parts if part]
        elif isinstance(value, (list, tuple, set)):
            for entry in value:
                if entry is None:
                    continue
                text = str(entry).strip()
                if text:
                    tags.append(text)

        unique: list[str] = []
        for tag in tags:
            if tag not in unique:
                unique.append(tag)
        return unique

    @staticmethod
    def _field_required(*, records: list[dict[str, Any]], field_key: str) -> bool:
        for record in records:
            if record.get("field_key") == field_key and SheinCategoryTreeSyncFactory._coerce_bool(value=record.get("required")):
                return True
        return False

    @staticmethod
    def _coerce_bool(*, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    def _ensure_remote_language(
        self,
        *,
        language_code: str,
    ) -> None:
        normalized_code = language_code.strip().lower()
        if not normalized_code:
            return

        cache_key = (self.sales_channel_id, normalized_code)
        if cache_key in self._remote_language_cache:
            return

        local_code = SUPPORTED_LANGUAGE_CODES.get(normalized_code)

        SheinRemoteLanguage.objects.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_code=normalized_code,
            defaults={
                "local_instance": local_code,
                "remote_name": self._resolve_language_name(language_code=normalized_code),
            },
        )

        self._remote_language_cache.add(cache_key)

    def _sync_product_type_attributes(
        self,
        *,
        product_type: SheinProductType,
    ) -> None:
        remote_id = self._normalize_identifier(product_type.remote_id)
        if remote_id is None:
            return

        category_permissions = self._get_category_custom_value_permissions(
            category_id=product_type.category_id,
        )

        attribute_records = self._attribute_template_cache.get(remote_id)
        if attribute_records is None:
            logger.info(
                "Attribute template cache miss for product type %s (channel=%s)",
                remote_id,
                self.sales_channel_id,
            )
            self._print_debug(f"Attribute template cache miss for product type {remote_id}.")
            attribute_records = self._fetch_attribute_template(product_type_id=remote_id)
            self._attribute_template_cache[remote_id] = attribute_records
        else:
            logger.info(
                "Attribute template cache hit for product type %s (channel=%s)",
                remote_id,
                self.sales_channel_id,
            )
            self._print_debug(f"Attribute template cache hit for product type {remote_id}.")

        if not attribute_records:
            logger.info(
                "No attribute definitions returned for product type %s (channel=%s)",
                remote_id,
                self.sales_channel_id,
            )
            self._print_debug(f"No attribute definitions returned for product type {remote_id}.")
            return

        seen_property_ids: set[int] = set()

        logger.info(
            "Syncing %s attribute definitions for product type %s (category=%s, channel=%s)",
            len(attribute_records),
            remote_id,
            product_type.category_id or "n/a",
            self.sales_channel_id,
        )
        self._print_debug(
            f"Syncing {len(attribute_records)} attributes for product type {remote_id} (category={product_type.category_id or 'n/a'})."
        )
        for attribute in attribute_records:
            if not isinstance(attribute, dict):
                continue

            property_obj = self._sync_property_definition(attribute=attribute)
            if property_obj is None:
                continue

            seen_property_ids.add(property_obj.pk)
            self._sync_property_select_values(property_obj=property_obj, attribute=attribute)
            self._sync_product_type_item(
                product_type=product_type,
                property_obj=property_obj,
                attribute=attribute,
                category_permissions=category_permissions,
            )

        if seen_property_ids:
            (
                SheinProductTypeItem.objects.filter(product_type=product_type)
                .exclude(property_id__in=seen_property_ids)
                .delete()
            )
        logger.info(
            "Finished syncing product type %s: %s attributes mapped (channel=%s)",
            remote_id,
            len(seen_property_ids),
            self.sales_channel_id,
        )
        self._print_debug(
            f"Finished product type {remote_id}: mapped {len(seen_property_ids)} attributes."
        )

    def _get_category_custom_value_permissions(
        self,
        *,
        category_id: Optional[str],
    ) -> dict[str, bool]:
        normalized_category = self._normalize_identifier(category_id)
        if not normalized_category:
            return {}

        cached = self._custom_value_permission_cache.get(normalized_category)
        if cached is None:
            logger.info(
                "Fetching custom value permissions for category %s (channel=%s)",
                normalized_category,
                self.sales_channel_id,
            )
            self._print_debug(
                f"Fetching custom attribute permissions for category {normalized_category}."
            )
            cached = self._fetch_custom_attribute_permissions(category_id=normalized_category)
            self._custom_value_permission_cache[normalized_category] = cached
        else:
            logger.info(
                "Using cached custom value permissions for category %s (channel=%s)",
                normalized_category,
                self.sales_channel_id,
            )
            self._print_debug(
                f"Using cached custom attribute permissions for category {normalized_category}."
            )

        return cached

    def _fetch_attribute_template(self, *, product_type_id: str) -> list[dict[str, Any]]:
        payload = {"product_type_id_list": [self._coerce_int(value=product_type_id)]}
        logger.info(
            "Requesting attribute template for product type %s (channel=%s)",
            product_type_id,
            self.sales_channel_id,
        )
        self._print_debug(f"Requesting attribute template for product type {product_type_id}.")

        try:
            response = self.shein_post(path=self.attribute_template_path, payload=payload)
        except ValueError:
            logger.exception(
                "Failed to retrieve Shein attribute template for product type %s",
                product_type_id,
            )
            return []

        try:
            data = response.json()
        except ValueError:
            logger.exception(
                "Invalid JSON while fetching Shein attribute template for product type %s",
                product_type_id,
            )
            return []

        if not isinstance(data, dict):
            return []

        info = data.get("info")
        if not isinstance(info, dict):
            return []

        records = info.get("data")
        if not isinstance(records, list):
            return []

        normalized_remote_id = str(product_type_id)
        for record in records:
            if not isinstance(record, dict):
                continue
            record_product_type_id = self._normalize_identifier(record.get("product_type_id"))
            if record_product_type_id != normalized_remote_id:
                continue

            attribute_infos = record.get("attribute_infos")
            if isinstance(attribute_infos, list):
                attributes = [info for info in attribute_infos if isinstance(info, dict)]
                logger.info(
                    "Received %s attribute definitions for product type %s (channel=%s)",
                    len(attributes),
                    product_type_id,
                    self.sales_channel_id,
                )
                self._print_debug(
                    f"Received {len(attributes)} attribute definitions for product type {product_type_id}."
                )
                return attributes

        logger.info(
            "Attribute template response did not include product type %s (channel=%s)",
            product_type_id,
            self.sales_channel_id,
        )
        self._print_debug(
            f"Attribute template response missing product type {product_type_id}."
        )
        return []

    def _fetch_custom_attribute_permissions(
        self,
        *,
        category_id: str,
    ) -> dict[str, bool]:
        payload = {"category_id_list": [self._coerce_int(value=category_id)]}
        logger.info(
            "Requesting custom attribute permissions for category %s (channel=%s)",
            category_id,
            self.sales_channel_id,
        )
        self._print_debug(f"Requesting custom attribute permissions for category {category_id}.")

        try:
            response = self.shein_post(
                path=self.custom_attribute_permission_path,
                payload=payload,
            )
        except ValueError:
            logger.exception(
                "Failed to retrieve Shein custom attribute permissions for category %s",
                category_id,
            )
            return {}

        try:
            data = response.json()
        except ValueError:
            logger.exception(
                "Invalid JSON while fetching Shein custom attribute permissions for category %s",
                category_id,
            )
            return {}

        if not isinstance(data, dict):
            return {}

        info = data.get("info")
        if not isinstance(info, dict):
            return {}

        records = info.get("data")
        if not isinstance(records, list):
            return {}

        normalized_category = self._normalize_identifier(category_id)
        permissions: dict[str, bool] = {}
        for record in records:
            if not isinstance(record, dict):
                continue

            record_category = self._normalize_identifier(record.get("last_category_id"))
            if normalized_category and record_category != normalized_category:
                continue

            attribute_id = self._normalize_identifier(record.get("attribute_id"))
            if not attribute_id:
                continue

            permissions[attribute_id] = self._to_bool(record.get("has_permission"))

        logger.info(
            "Received %s custom attribute permission entries for category %s (channel=%s)",
            len(permissions),
            category_id,
            self.sales_channel_id,
        )
        self._print_debug(
            f"Received {len(permissions)} custom attribute permission entries for category {category_id}."
        )
        return permissions

    def _sync_property_definition(
        self,
        *,
        attribute: dict[str, Any],
    ) -> Optional[SheinProperty]:
        remote_id = self._normalize_identifier(attribute.get("attribute_id"))
        if remote_id is None:
            return None

        attribute_mode = self._safe_int(value=attribute.get("attribute_mode"))
        raw_attribute = self._strip_attribute_values(attribute=attribute)

        defaults = {
            "name": self._strip_openapi_prefix(self._safe_string(attribute.get("attribute_name"))),
            "name_en": self._strip_openapi_prefix(self._safe_string(attribute.get("attribute_name_en"))),
            "value_mode": SheinProperty.ValueModes.from_remote(raw_value=attribute_mode),
            "value_limit": self._safe_positive_int(value=attribute.get("attribute_input_num")),
            "attribute_source": self._safe_int(value=attribute.get("attribute_source")),
            "data_dimension": self._safe_int(value=attribute.get("data_dimension")),
            "business_mode": self._safe_int(value=attribute.get("business_mode")),
            "is_sample": self._to_bool(attribute.get("is_sample")),
            "supplier_id": self._safe_string(attribute.get("supplier_id")) or "",
            "attribute_doc": self._safe_string(attribute.get("attribute_doc")) or "",
            "attribute_doc_images": self._ensure_list(value=attribute.get("attribute_doc_image_list")),
            "allows_unmapped_values": SheinProperty.allows_custom_values(attribute_mode=attribute_mode),
            "raw_data": raw_attribute,
        }

        property_obj, created = SheinProperty.objects.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=remote_id,
            defaults=defaults,
        )

        if created:
            property_obj.type = SheinProperty.determine_property_type(attribute_mode=attribute_mode)
            property_obj.save(update_fields=["type"])

        return property_obj

    def _sync_property_select_values(
        self,
        *,
        property_obj: SheinProperty,
        attribute: dict[str, Any],
    ) -> None:
        values = attribute.get("attribute_value_info_list")
        if not isinstance(values, list):
            return

        for value_record in values:
            if not isinstance(value_record, dict):
                continue

            remote_id = self._normalize_identifier(value_record.get("attribute_value_id"))
            if remote_id is None:
                continue

            defaults = {
                "value": self._safe_string(value_record.get("attribute_value")) or "",
                "value_en": self._safe_string(value_record.get("attribute_value_en")) or "",
                "is_custom_value": self._to_bool(value_record.get("is_custom_attribute_value")),
                "is_visible": self._to_bool(value_record.get("is_show")),
                "supplier_id": self._safe_string(value_record.get("supplier_id")) or "",
                "documentation": self._safe_string(value_record.get("attribute_value_doc")) or "",
                "documentation_images": self._ensure_list(value=value_record.get("attribute_value_doc_image_list")),
                "group_data": self._ensure_list(value=value_record.get("attribute_value_group_list")),
                "raw_data": value_record,
            }

            SheinPropertySelectValue.objects.update_or_create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_property=property_obj,
                remote_id=remote_id,
                defaults=defaults,
            )

    def _sync_product_type_item(
        self,
        *,
        product_type: SheinProductType,
        property_obj: SheinProperty,
        attribute: dict[str, Any],
        category_permissions: dict[str, bool],
    ) -> None:
        identifier = self._build_product_type_item_identifier(
            product_type=product_type,
            property_obj=property_obj,
        )
        remarks = SheinProductTypeItem.RemarkTags.normalize(
            values=attribute.get("attribute_remark_list"),
        )

        allows_custom_values = category_permissions.get(
            self._normalize_identifier(property_obj.remote_id),
            False,
        )

        approved_value_ids = [
            str(self._normalize_identifier(record.get("attribute_value_id")))
            for record in attribute.get("attribute_value_info_list") or []
            if isinstance(record, dict) and self._normalize_identifier(record.get("attribute_value_id"))
        ]
        raw_data = self._strip_attribute_values(attribute=attribute)

        SheinProductTypeItem.objects.update_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            product_type=product_type,
            property=property_obj,
            defaults={
                "sales_channel": self.sales_channel,
                "remote_id": identifier,
                "visibility": SheinProductTypeItem.Visibility.from_remote(
                    raw_value=attribute.get("attribute_is_show")
                ),
                "attribute_type": SheinProductTypeItem.AttributeType.from_remote(
                    raw_value=attribute.get("attribute_type")
                ),
                "requirement": SheinProductTypeItem.Requirement.from_remote(
                    raw_value=attribute.get("attribute_status")
                ),
                "is_main_attribute": self._to_bool(attribute.get("attribute_label")),
                "allows_unmapped_values": allows_custom_values,
                "remarks": remarks,
                "approved_value_ids": approved_value_ids,
                "raw_data": raw_data,
            },
        )

    def _fetch_publish_fill_in_standard(self, *, category_id: Optional[str]) -> Optional[dict[str, Any]]:
        if not category_id:
            return None

        payload = {"category_id": category_id}
        logger.info(
            "Requesting publish fill-in standard for category %s (channel=%s)",
            category_id,
            self.sales_channel_id,
        )
        self._print_debug(f"Requesting publish fill-in standard for category {category_id}.")

        try:
            response = self.shein_post(path=self.publish_standard_path, payload=payload)
        except ValueError:
            logger.exception(
                "Failed to retrieve Shein publish fill-in standard for category %s",
                category_id,
            )
            return None

        try:
            data = response.json()
        except ValueError:
            logger.exception(
                "Invalid JSON while fetching Shein publish fill-in standard for category %s",
                category_id,
            )
            return None

        if not isinstance(data, dict):
            return None

        info = data.get("info")
        if not isinstance(info, dict):
            return None

        logger.info(
            "Received publish standard payload for category %s (channel=%s)",
            category_id,
            self.sales_channel_id,
        )
        self._print_debug(
            f"Received publish fill-in standard for category {category_id}."
        )
        return info

    def _build_product_type_item_identifier(
        self,
        *,
        product_type: SheinProductType,
        property_obj: SheinProperty,
    ) -> str:
        product_type_id = self._safe_string(product_type.remote_id) or ""
        property_id = self._safe_string(property_obj.remote_id) or ""

        if product_type_id and property_id:
            identifier = f"{product_type_id}:{property_id}"
        else:
            identifier = property_id or product_type_id or ""

        return identifier[:255]

    def _resolve_language_name(
        self,
        *,
        language_code: str,
    ) -> Optional[str]:
        normalized_code = language_code.strip().lower()
        domain = self._get_view_domain()

        if domain:
            for entry in constants.SHEIN_LANGUAGE_CATALOG:
                entry_code = str(entry.get("language_code", "")).strip().lower()
                entry_domain = self._normalise_domain(value=entry.get("shein_domain"))
                if entry_code == normalized_code and entry_domain == domain:
                    return self._safe_string(entry.get("language_name"))

        for entry in constants.SHEIN_LANGUAGE_CATALOG:
            entry_code = str(entry.get("language_code", "")).strip().lower()
            if entry_code == normalized_code:
                return self._safe_string(entry.get("language_name"))

        return None

    def _get_view_domain(self) -> Optional[str]:
        return self._normalise_domain(value=getattr(self.sales_channel, "hostname", None))

    @staticmethod
    def _normalize_picture_config(data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, list):
            return []

        normalized: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            cleaned_entry = {
                str(key): entry[key]
                for key in entry
            }
            normalized.append(cleaned_entry)
        return normalized

    def _build_request_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.language:
            payload["language"] = self.language
        return payload

    @staticmethod
    def _prepare_raw_payload(*, node: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in node.items() if key != "children"}

    @staticmethod
    def _normalize_identifier(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _safe_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _strip_openapi_prefix(value: Optional[str]) -> str:
        if not value:
            return ""
        text = value.strip()
        prefix = "OPENAPI-"
        if text.upper().startswith(prefix):
            return text[len(prefix):].lstrip()
        return text

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return False

    @staticmethod
    def _strip_attribute_values(*, attribute: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in attribute.items()
            if key != "attribute_value_info_list"
        }

    @staticmethod
    def _ensure_list(*, value: Any) -> list[Any]:
        if isinstance(value, list):
            return [entry for entry in value]
        return []

    @staticmethod
    def _safe_int(*, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            text = str(value).strip()
            if not text:
                return None
            return int(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_positive_int(*, value: Any) -> Optional[int]:
        numeric = SheinCategoryTreeSyncFactory._safe_int(value=value)
        if numeric is None:
            return None
        return numeric if numeric >= 0 else None

    @staticmethod
    def _coerce_int(*, value: Any) -> Any:
        try:
            text = str(value).strip()
            if not text:
                return value
            return int(text)
        except (TypeError, ValueError):
            return value

    @staticmethod
    def _normalise_domain(*, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        candidate = value.strip()
        if not candidate:
            return None

        if "//" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        domain = parsed.netloc or parsed.path
        domain = domain.strip().lower()
        return domain or None
