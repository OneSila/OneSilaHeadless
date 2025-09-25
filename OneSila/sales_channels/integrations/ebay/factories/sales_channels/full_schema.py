"""Factories for building eBay product type rules."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any, Optional

from properties.models import Property, ProductPropertiesRuleItem
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import (
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannel,
    EbaySalesChannelView,
)


logger = logging.getLogger(__name__)


class EbayProductTypeRuleFactory(GetEbayAPIMixin):
    """Build local mirrors of eBay product type metadata for a given category."""

    def __init__(
        self,
        *,
        sales_channel: EbaySalesChannel,
        view: EbaySalesChannelView,
        category_id: str,
        category_tree_id: Optional[str] = None,
        language: Optional[str] = None,
        category_aspects: Optional[dict[str, set[str]]] = None,
    ) -> None:
        self.sales_channel = sales_channel
        self.view = self._ensure_real_view(view)
        self.category_id = str(category_id) if category_id is not None else None
        self.category_tree_id = category_tree_id or getattr(self.view, "default_category_tree_id", None)
        self.language = language
        self.multi_tenant_company = sales_channel.multi_tenant_company
        normalized_category_aspects: dict[str, set[str]] = {}
        for aspect_name, values in (category_aspects or {}).items():
            if not aspect_name:
                continue

            if isinstance(values, set):
                normalized_values = {str(value) for value in values if value is not None}
            elif isinstance(values, Iterable) and not isinstance(values, (str, bytes, bytearray)):
                normalized_values = {str(value) for value in values if value is not None}
            else:
                continue

            if not normalized_values:
                continue

            normalized_category_aspects[str(aspect_name)] = normalized_values
        self.category_aspects = normalized_category_aspects

        # Each factory instance needs its own API configured for the specific view headers.
        self.api = self.get_api()

    def run(self) -> None:
        """Build local product type rules for the configured category."""

        if not self.category_id:
            logger.warning("Skipping eBay product type sync because category_id is missing.")
            return

        if not self.category_tree_id:
            logger.warning(
                "Skipping eBay product type sync for category %s due to missing category tree id.",
                self.category_id,
            )
            return

        category_data = self._fetch_category_details()
        print('------------------------------------------')
        print(category_data)
        product_type = self._get_or_create_product_type(category_data)
        if product_type is None:
            return

        aspects = self._fetch_aspects()
        if not aspects:
            return

        # print('--------------------------------------------------- ASPECTS')
        # import pprint
        # pprint.pprint(aspects)
        for aspect in aspects:
            ebay_property = self._sync_property(product_type, aspect)
            if ebay_property is None:
                continue
            self._sync_product_type_item(product_type, ebay_property, aspect)

    @staticmethod
    def _ensure_real_view(view: EbaySalesChannelView) -> EbaySalesChannelView:
        """Return the concrete EbaySalesChannelView instance for polymorphic wrappers."""

        real_view_getter = getattr(view, "get_real_instance", None)
        if callable(real_view_getter):
            real_view = real_view_getter()
            if isinstance(real_view, EbaySalesChannelView):
                return real_view
        return view

    def _fetch_category_details(self) -> dict[str, Any] | None:
        """Return basic information about the configured category."""

        try:
            response = self.api.commerce_taxonomy_get_category_subtree(
                category_id=self.category_id,
                category_tree_id=self.category_tree_id,
            )
            print('--------------------------------- RESPONSE DETAILS')
            print(response)
        except Exception:  # pragma: no cover - defensive logging
            logger.exception(
                "Failed to fetch eBay category subtree for category %s in tree %s",
                self.category_id,
                self.category_tree_id,
            )
            return None

        if not isinstance(response, dict):
            return None

        node = response.get("category_subtree_node")
        if isinstance(node, dict):
            category = node.get("category")
            if isinstance(category, dict):
                return category
            return node
        return None

    def _fetch_aspects(self) -> list[dict[str, Any]]:
        """Fetch aspect metadata for the configured category."""

        try:
            response = self.api.commerce_taxonomy_get_item_aspects_for_category(
                category_id=self.category_id,
                category_tree_id=self.category_tree_id,
            )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception(
                "Failed to fetch eBay aspects for category %s in tree %s",
                self.category_id,
                self.category_tree_id,
            )
            return []

        if isinstance(response, dict):
            aspects = response.get("aspects")
            if isinstance(aspects, list):
                return [aspect for aspect in aspects if isinstance(aspect, dict)]
        return []

    def _get_or_create_product_type(self, category: dict[str, Any] | None) -> EbayProductType | None:
        """Create or update the EbayProductType record for the current category."""

        remote_id = self.category_id
        name = None
        if category:
            category_id = category.get("category_id")
            if category_id is not None:
                remote_id = str(category_id)
            name = category.get("category_name")

        if remote_id is None:
            logger.warning("Unable to determine remote_id for eBay category. Skipping sync.")
            return None

        defaults: dict[str, Any] = {}
        if name:
            defaults["name"] = name

        print('------------------------------------------ NAME')
        print(name)

        product_type, _ = EbayProductType.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            marketplace=self.view,
            remote_id=str(remote_id),
            defaults=defaults,
        )

        update_fields: list[str] = []
        if product_type.marketplace_id != getattr(self.view, "id", None):
            product_type.marketplace = self.view
            update_fields.append("marketplace")

        if name and product_type.name != name:
            product_type.name = name
            update_fields.append("name")
        if update_fields:
            product_type.save(update_fields=update_fields)

        return product_type

    def _sync_property(
        self,
        product_type: EbayProductType,
        aspect: dict[str, Any],
    ) -> EbayProperty | None:
        localized_name = aspect.get("localized_aspect_name")
        if not localized_name:
            return None

        constraint = aspect.get("aspect_constraint") or {}
        applicable_to = constraint.get("aspect_applicable_to")
        if isinstance(applicable_to, list) and "PRODUCT" not in applicable_to:
            return None

        aspect_values = aspect.get("aspect_values") or []
        aspect_format = constraint.get("aspect_format")
        property_type, allows_unmapped = self._determine_property_metadata(aspect, aspect_values)

        ebay_property, _ = EbayProperty.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            marketplace=self.view,
            localized_name=localized_name,
        )

        update_fields: list[str] = []
        aspect_id = aspect.get("aspect_id")
        if aspect_id is not None:
            aspect_id = str(aspect_id)
            if ebay_property.remote_id != aspect_id:
                ebay_property.remote_id = aspect_id
                update_fields.append("remote_id")

        if ebay_property.type != property_type:
            ebay_property.type = property_type
            update_fields.append("type")

        if ebay_property.allows_unmapped_values != allows_unmapped:
            ebay_property.allows_unmapped_values = allows_unmapped
            update_fields.append("allows_unmapped_values")

        normalized_format = aspect_format or None
        if ebay_property.value_format != normalized_format:
            ebay_property.value_format = normalized_format
            update_fields.append("value_format")

        if ebay_property.raw_data != aspect:
            ebay_property.raw_data = aspect
            update_fields.append("raw_data")

        if update_fields:
            ebay_property.save(update_fields=update_fields)

        allowed_values = self.category_aspects.get(localized_name)
        self._sync_property_values(
            ebay_property=ebay_property,
            aspect_values=aspect_values,
            allows_unmapped=allows_unmapped,
            allowed_values=allowed_values,
        )

        return ebay_property

    def _sync_property_values(
        self,
        *,
        ebay_property: EbayProperty,
        aspect_values: list[Any],
        allows_unmapped: bool,
        allowed_values: Optional[set[str]],
    ) -> None:
        if ebay_property.type not in {Property.TYPES.SELECT, Property.TYPES.MULTISELECT}:
            return

        allowed_lookup: set[str] | None = None
        if allows_unmapped:
            if not allowed_values:
                return
            allowed_lookup = {str(value) for value in allowed_values if value is not None}

        for value_data in aspect_values or []:
            if not isinstance(value_data, dict):
                continue
            localized_value = value_data.get("localized_value")
            if localized_value in {None, ""}:
                continue

            if not isinstance(localized_value, str):
                localized_value = str(localized_value)

            if allowed_lookup is not None and localized_value not in allowed_lookup:
                continue

            value_obj, _ = EbayPropertySelectValue.objects.get_or_create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
                ebay_property=ebay_property,
                marketplace=self.view,
                localized_value=localized_value,
            )

            remote_value_id = value_data.get("value_id") or value_data.get("value")
            if remote_value_id is not None:
                remote_value_id = str(remote_value_id)
                if value_obj.remote_id != remote_value_id:
                    value_obj.remote_id = remote_value_id
                    value_obj.save(update_fields=["remote_id"])

    def _sync_product_type_item(
        self,
        product_type: EbayProductType,
        ebay_property: EbayProperty,
        aspect: dict[str, Any],
    ) -> None:
        constraint = aspect.get("aspect_constraint") or {}
        remote_type = self._determine_remote_type(constraint)

        rule_item, _ = EbayProductTypeItem.objects.get_or_create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            product_type=product_type,
            ebay_property=ebay_property,
        )

        if rule_item.remote_type != remote_type:
            rule_item.remote_type = remote_type
            rule_item.save(update_fields=["remote_type"])

    def _determine_property_metadata(
        self,
        aspect: dict[str, Any],
        aspect_values: list[Any],
    ) -> tuple[str, bool]:
        constraint = aspect.get("aspect_constraint") or {}
        data_type = (constraint.get("aspect_data_type") or "").upper()
        mode = (constraint.get("aspect_mode") or "").upper()
        cardinality = (constraint.get("item_to_aspect_cardinality") or "").upper()
        advanced_data_type = (constraint.get("aspect_advanced_data_type") or "").upper()
        max_length = self._to_int(constraint.get("aspect_max_length"))
        aspect_format = constraint.get("aspect_format")

        # Default values
        property_type = Property.TYPES.TEXT
        allows_unmapped = True

        if mode == "FREE_TEXT" and advanced_data_type == "NUMERIC_RANGE":
            return Property.TYPES.TEXT, allows_unmapped

        if data_type == "NUMBER":
            format_lower = (aspect_format or "").lower()
            if format_lower == "double":
                return Property.TYPES.FLOAT, allows_unmapped
            return Property.TYPES.INT, allows_unmapped

        if data_type == "DATE":
            if self._is_datetime_format(aspect_format):
                return Property.TYPES.DATETIME, allows_unmapped
            return Property.TYPES.DATE, allows_unmapped

        if aspect_values:
            allows_unmapped = mode != "SELECTION_ONLY"
            if cardinality == "MULTI":
                property_type = Property.TYPES.MULTISELECT
            else:
                property_type = Property.TYPES.SELECT
            return property_type, allows_unmapped

        if mode == "FREE_TEXT":
            if max_length is not None and max_length > 800:
                return Property.TYPES.DESCRIPTION, allows_unmapped
            return Property.TYPES.TEXT, allows_unmapped

        return property_type, allows_unmapped

    @staticmethod
    def _is_datetime_format(aspect_format: Any) -> bool:
        if not aspect_format or not isinstance(aspect_format, str):
            return False
        fmt_lower = aspect_format.lower()
        return any(token in fmt_lower for token in ("hh", "ss")) or ":" in aspect_format or "t" in fmt_lower or " " in aspect_format

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_bool(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"true", "false"}:
                return lowered == "true"
        return None

    def _determine_remote_type(self, constraint: dict[str, Any]) -> Optional[str]:
        variations = self._normalize_bool(constraint.get("aspect_enabled_for_variations"))
        required = self._normalize_bool(constraint.get("aspect_required"))
        usage = (constraint.get("aspect_usage") or "").upper()

        if variations:
            if required:
                return ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
            return ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR

        if required:
            if usage in {"", "RECOMMENDED"}:
                return ProductPropertiesRuleItem.REQUIRED
            return ProductPropertiesRuleItem.REQUIRED

        if required is False:
            return ProductPropertiesRuleItem.OPTIONAL

        return ProductPropertiesRuleItem.OPTIONAL
