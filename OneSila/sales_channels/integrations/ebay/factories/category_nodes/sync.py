from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbayCategory, EbaySalesChannelView


@dataclass
class _CategoryEntry:
    remote_id: str
    name: str


class EbayCategoryNodeSyncFactory(GetEbayAPIMixin):
    """Persist eBay category tree leaves for quick lookups."""

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
        ancestors: tuple[str, ...] = (),
    ) -> Iterator[_CategoryEntry]:
        category = node.get("category") or {}
        if not isinstance(category, dict):
            category = {}

        raw_id = category.get("categoryId") or category.get("category_id")
        raw_name = category.get("categoryName") or category.get("category_name")
        node_id = str(raw_id).strip() if raw_id is not None else ""
        node_name = str(raw_name).strip() if raw_name is not None else ""

        path_parts = tuple(part for part in (*ancestors, node_name) if part)

        if node_id and path_parts:
            yield _CategoryEntry(
                remote_id=node_id,
                name=" > ".join(path_parts),
            )

        children = node.get("childCategoryTreeNodes") or node.get("child_category_tree_nodes") or []
        for child in children if isinstance(children, Iterable) else []:
            if isinstance(child, dict):
                yield from self._walk_nodes(child, path_parts)

    def _persist_nodes(self, nodes: list[_CategoryEntry]) -> None:
        marketplace_id = self.category_tree_id
        existing = {
            obj.remote_id: obj
            for obj in EbayCategory.objects.filter(marketplace_default_tree_id=marketplace_id)
        }

        new_objects: list[EbayCategory] = []
        to_update: list[EbayCategory] = []
        seen_ids: set[str] = set()

        for entry in nodes:
            seen_ids.add(entry.remote_id)

            if entry.remote_id in existing:
                obj = existing[entry.remote_id]
                updated = False
                if obj.name != entry.name:
                    obj.name = entry.name
                    updated = True
                if updated:
                    to_update.append(obj)
                continue

            new_objects.append(
                EbayCategory(
                    remote_id=entry.remote_id,
                    marketplace_default_tree_id=marketplace_id,
                    name=entry.name,
                )
            )

        if new_objects:
            EbayCategory.objects.bulk_create(new_objects, ignore_conflicts=True)

        if to_update:
            EbayCategory.objects.bulk_update(
                to_update,
                ["name"],
            )

        stale_ids = set(existing) - seen_ids
        if stale_ids:
            EbayCategory.objects.filter(
                marketplace_default_tree_id=marketplace_id,
                remote_id__in=stale_ids,
            ).delete()
