"""Factories to mirror Shein category trees and product types locally."""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.db import transaction

from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinProductType,
    SheinSalesChannel,
    SheinSalesChannelView,
)


logger = logging.getLogger(__name__)


class SheinCategoryTreeSyncFactory(SheinSignatureMixin):
    """Fetch and persist the full category tree for a Shein storefront."""

    category_tree_path = "/open-api/goods/query-category-tree"

    def __init__(
        self,
        *,
        sales_channel: SheinSalesChannel,
        view: Optional[SheinSalesChannelView] = None,
        language: Optional[str] = None,
    ) -> None:
        self.sales_channel = sales_channel
        self.sales_channel_id = getattr(sales_channel, "pk", None)
        self.view = view
        self.site_remote_id = self._normalize_identifier(getattr(view, "remote_id", None)) if view else ""
        self.language = language
        self.synced_categories: list[SheinCategory] = []
        self.synced_product_types: list[SheinProductType] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, *, tree: Optional[list[dict[str, Any]]] = None) -> list[SheinCategory]:
        """Fetch the remote tree (when not provided) and persist all nodes."""

        nodes = tree if tree is not None else self.fetch_remote_category_tree()
        normalized_nodes = [node for node in nodes if isinstance(node, dict)]

        self.synced_categories = []
        self.synced_product_types = []

        if not normalized_nodes:
            return []

        with transaction.atomic():
            for node in normalized_nodes:
                self._sync_node(node=node, parent=None)

        return self.synced_categories

    def fetch_remote_category_tree(self) -> list[dict[str, Any]]:
        """Call Shein and return the raw category tree."""

        payload = self._build_request_payload()

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

        return [record for record in records if isinstance(record, dict)]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sync_node(self, *, node: dict[str, Any], parent: Optional[SheinCategory]) -> None:
        category = self._sync_category(node=node, parent=parent)
        if category is None:
            return

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
            "site_remote_id": self.site_remote_id or "",
        }

        category, _ = SheinCategory.objects.update_or_create(
            remote_id=remote_id,
            site_remote_id=self.site_remote_id or "",
            defaults=defaults,
        )

        self.synced_categories.append(category)

        product_type = self._sync_product_type(category=category, node=node)
        if product_type is not None:
            self.synced_product_types.append(product_type)

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
            "category": category,
            "name": self._safe_string(node.get("category_name")),
            "is_leaf": self._to_bool(node.get("last_category")),
            "raw_data": self._prepare_raw_payload(node=node),
            "imported": True,
        }

        product_type, _ = SheinProductType.objects.update_or_create(
            sales_channel=self.sales_channel,
            view=self.view,
            remote_id=remote_id,
            defaults=defaults,
        )

        return product_type

    def _build_request_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.site_remote_id:
            payload["site_abbr"] = self.site_remote_id
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
