from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Optional

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbayCategory, EbaySalesChannelView


@dataclass
class _CategoryEntry:
    remote_id: str
    name: str
    full_name: str
    has_children: bool
    is_root: bool
    parent_remote_id: Optional[str]


class EbayCategoryNodeSyncFactory(GetEbayAPIMixin):
    """Persist eBay category tree nodes for quick lookups."""

    def __init__(self, *, view: EbaySalesChannelView) -> None:
        self.view = view
        self.category_tree_id = (getattr(view, "default_category_tree_id", None) or "").strip()
        self.sales_channel = view.sales_channel
        get_real_instance = getattr(self.sales_channel, "get_real_instance", None)
        if callable(get_real_instance):
            self.sales_channel = get_real_instance()
        self.api = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        if not self.sales_channel or not self.category_tree_id:
            return

        if not self._configure_api():
            return

        payload = self._fetch_payload()
        if not payload:
            return

        entries = list(self._extract_entries(payload))
        if not entries:
            return

        self._persist_nodes(entries)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _configure_api(self) -> bool:
        try:
            self.api = self.get_api()
        except Exception:
            self.api = None
            return False
        return self.api is not None

    def _fetch_payload(self) -> dict[str, object]:
        if self.api is None:
            return {}

        try:
            response = self.api.commerce_taxonomy_get_category_tree(
                category_tree_id=self.category_tree_id,
                accept_encoding="gzip",
            )
        except Exception:
            return {}

        return self._to_dict(response)

    def _to_dict(self, payload: object) -> dict[str, object]:
        if isinstance(payload, dict):
            return payload

        to_dict = getattr(payload, "to_dict", None)
        if callable(to_dict):
            try:
                data = to_dict()
                if isinstance(data, dict):
                    return data
            except Exception:
                return {}
        return {}

    def _extract_entries(self, payload: dict[str, object]) -> Iterator[_CategoryEntry]:
        root_node = payload.get("rootCategoryNode") or payload.get("root_category_node")
        if not isinstance(root_node, dict):
            return iter(())
        return self._walk_nodes(root_node)

    def _walk_nodes(
        self,
        node: dict[str, object],
        ancestor_names: tuple[str, ...] = (),
        ancestor_ids: tuple[str, ...] = (),
    ) -> Iterator[_CategoryEntry]:
        category = node.get("category") or {}
        if not isinstance(category, dict):
            category = {}

        raw_id = category.get("categoryId") or category.get("category_id")
        raw_name = category.get("categoryName") or category.get("category_name")
        node_id = str(raw_id).strip() if raw_id is not None else ""
        node_name = str(raw_name).strip() if raw_name is not None else ""

        path_parts = tuple(part for part in (*ancestor_names, node_name) if part)

        children = node.get("childCategoryTreeNodes") or node.get("child_category_tree_nodes") or []
        if isinstance(children, Iterable):
            child_nodes = [child for child in children if isinstance(child, dict)]
        else:
            child_nodes = []
        has_children = bool(child_nodes)

        parent_remote_id = ancestor_ids[-1] if ancestor_ids else None
        is_root = not ancestor_ids

        if node_id and path_parts:
            yield _CategoryEntry(
                remote_id=node_id,
                name=node_name,
                full_name=" > ".join(path_parts),
                has_children=has_children,
                is_root=is_root,
                parent_remote_id=parent_remote_id,
            )

        if child_nodes:
            next_ancestor_ids = (*ancestor_ids, node_id)
            next_ancestor_names = path_parts
            for child in child_nodes:
                yield from self._walk_nodes(child, next_ancestor_names, next_ancestor_ids)

    def _persist_nodes(self, nodes: list[_CategoryEntry]) -> None:
        marketplace_id = self.category_tree_id
        existing = {
            obj.remote_id: obj
            for obj in EbayCategory.objects.filter(marketplace_default_tree_id=marketplace_id)
        }

        new_objects: list[EbayCategory] = []
        to_update: list[EbayCategory] = []
        seen_ids: set[str] = set()
        parent_links: dict[str, Optional[str]] = {}

        for entry in nodes:
            seen_ids.add(entry.remote_id)
            parent_links[entry.remote_id] = entry.parent_remote_id

            if entry.has_children:
                configurator_properties: list[str] = []
            else:
                configurator_properties = self._fetch_configurator_properties(
                    category_id=entry.remote_id,
                )

            if entry.remote_id in existing:
                obj = existing[entry.remote_id]
                updated = False
                if obj.name != entry.name:
                    obj.name = entry.name
                    updated = True
                if obj.full_name != entry.full_name:
                    obj.full_name = entry.full_name
                    updated = True
                if obj.has_children != entry.has_children:
                    obj.has_children = entry.has_children
                    updated = True
                if obj.is_root != entry.is_root:
                    obj.is_root = entry.is_root
                    updated = True
                if obj.configurator_properties != configurator_properties:
                    obj.configurator_properties = configurator_properties
                    updated = True
                if updated:
                    to_update.append(obj)
                continue

            new_objects.append(
                EbayCategory(
                    remote_id=entry.remote_id,
                    marketplace_default_tree_id=marketplace_id,
                    name=entry.name,
                    full_name=entry.full_name,
                    has_children=entry.has_children,
                    is_root=entry.is_root,
                    configurator_properties=configurator_properties,
                )
            )

        if new_objects:
            EbayCategory.objects.bulk_create(new_objects, ignore_conflicts=True)

        if to_update:
            EbayCategory.objects.bulk_update(
                to_update,
                ["name", "full_name", "has_children", "is_root", "configurator_properties"],
            )

        refreshed_objects = {
            obj.remote_id: obj
            for obj in EbayCategory.objects.filter(
                marketplace_default_tree_id=marketplace_id,
                remote_id__in=seen_ids,
            )
        }

        parent_updates: list[EbayCategory] = []
        for remote_id, parent_remote_id in parent_links.items():
            obj = refreshed_objects.get(remote_id)
            if obj is None:
                continue
            desired_parent = refreshed_objects.get(parent_remote_id) if parent_remote_id else None
            desired_parent_id = desired_parent.id if desired_parent else None
            current_parent_id = obj.parent_node_id
            if current_parent_id != desired_parent_id:
                obj.parent_node = desired_parent
                parent_updates.append(obj)

        if parent_updates:
            EbayCategory.objects.bulk_update(parent_updates, ["parent_node"])

        stale_ids = set(existing) - seen_ids
        if stale_ids:
            EbayCategory.objects.filter(
                marketplace_default_tree_id=marketplace_id,
                remote_id__in=stale_ids,
            ).delete()

    def _fetch_configurator_properties(self, *, category_id: str) -> list[str]:
        if not category_id or self.api is None:
            return []

        try:
            response = self.api.commerce_taxonomy_get_item_aspects_for_category(
                category_id=category_id,
                category_tree_id=self.category_tree_id,
            )
        except Exception:
            return []

        payload = self._to_dict(response)
        aspects = payload.get("aspects")
        if not isinstance(aspects, list):
            return []

        names: list[str] = []
        for aspect in aspects:
            if not isinstance(aspect, dict):
                continue
            constraint = aspect.get("aspect_constraint") or aspect.get("aspectConstraint")
            if not isinstance(constraint, dict):
                constraint = {}

            enabled_raw = constraint.get("aspect_enabled_for_variations")
            if enabled_raw is None:
                enabled_raw = constraint.get("aspectEnabledForVariations")
            if not self._truthy(enabled_raw):
                continue

            localized_name = aspect.get("localized_aspect_name") or aspect.get("localizedAspectName")
            if localized_name is None:
                continue

            name = str(localized_name).strip()
            if not name:
                continue

            names.append(name)

        if not names:
            return []

        deduplicated: list[str] = []
        seen: set[str] = set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            deduplicated.append(name)

        return deduplicated

    def _truthy(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        if isinstance(value, (int, float)):
            return bool(value)
        return False
