from __future__ import annotations

from typing import Any

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayCategorySuggestionFactory(GetEbayAPIMixin):
    """Fetch and normalize eBay category suggestions or trees."""

    def __init__(self, *, view: Any, query: str) -> None:
        self.original_view = view
        self.view = self._resolve_view(view)
        self.sales_channel = self._resolve_sales_channel(self.view, view)
        self.query = query.strip()
        self.api = None
        self.category_tree_id: str = ""
        self.categories: list[dict[str, Any]] = []
        self._resolved_category_tree_id: str | None = None
        self._raw_payload: Any = {}
        self._normalized_payload: dict[str, Any] = {}

    def run(self) -> None:
        self._reset_state()
        if not self._resolve_context():
            return
        if not self._resolve_category_tree_id():
            return
        if not self.query:
            return
        if not self._configure_api():
            return
        self._fetch_payload()
        self._normalize_payload()
        self.categories = self._parse_suggestions(self._normalized_payload)
        self._finalize_category_tree_id()

    def _reset_state(self) -> None:
        self.categories = []
        self.category_tree_id = ""
        self._resolved_category_tree_id = None
        self._raw_payload = {}
        self._normalized_payload = {}
        self.api = None

    def _resolve_context(self) -> bool:
        return self.view is not None and self.sales_channel is not None

    def _resolve_category_tree_id(self) -> bool:
        category_tree_id = getattr(self.view, "default_category_tree_id", None)
        if not category_tree_id:
            return False

        self._resolved_category_tree_id = str(category_tree_id)
        return True

    def _configure_api(self) -> bool:
        try:
            self.api = self.get_api()
        except Exception:
            self.api = None
            return False

        return self.api is not None

    def _fetch_payload(self) -> None:
        if self._resolved_category_tree_id is None or not self.query or self.api is None:
            return

        try:
            self._raw_payload = self.api.commerce_taxonomy_get_category_suggestions(
                category_tree_id=self._resolved_category_tree_id,
                q=self.query,
            )
        except Exception:
            self._raw_payload = {}

    def _normalize_payload(self) -> None:
        self._normalized_payload = self._to_dict(self._raw_payload)

    def _finalize_category_tree_id(self) -> None:
        tree_id = None
        data = self._normalized_payload
        if isinstance(data, dict):
            tree_id = data.get("categoryTreeId") or data.get("category_tree_id")
        if tree_id is None:
            tree_id = self._resolved_category_tree_id

        self.category_tree_id = str(tree_id) if tree_id is not None else ""

    def _resolve_view(self, view: Any) -> EbaySalesChannelView | None:
        if isinstance(view, EbaySalesChannelView):
            return view

        getter = getattr(view, "get_real_instance", None)
        if callable(getter):
            real_view = getter()
            if isinstance(real_view, EbaySalesChannelView):
                return real_view

        pk = getattr(view, "pk", None)
        if pk is not None:
            return EbaySalesChannelView.objects.filter(pk=pk).first()
        return None

    def _resolve_sales_channel(
        self,
        resolved_view: EbaySalesChannelView | None,
        original_view: Any,
    ) -> EbaySalesChannel | None:
        candidate = None
        if resolved_view is not None:
            candidate = getattr(resolved_view, "sales_channel", None)
        if candidate is None and original_view is not None:
            candidate = getattr(original_view, "sales_channel", None)

        if isinstance(candidate, EbaySalesChannel):
            return candidate

        getter = getattr(candidate, "get_real_instance", None)
        if callable(getter):
            real_channel = getter()
            if isinstance(real_channel, EbaySalesChannel):
                return real_channel

        pk = getattr(candidate, "pk", None)
        if pk is not None:
            return EbaySalesChannel.objects.filter(pk=pk).first()
        return None

    def _to_dict(self, payload: Any) -> dict[str, Any]:
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

    def _build_entry(
        self,
        category: dict[str, Any],
        path_segments: list[str],
        leaf: bool,
    ) -> dict[str, Any] | None:
        category_id = category.get("categoryId")
        category_name = category.get("categoryName")
        if category_id is None or not category_name:
            return None
        category_path = " > ".join([segment for segment in path_segments if segment])
        return {
            "category_id": str(category_id),
            "category_name": category_name,
            "category_path": category_path,
            "leaf": bool(leaf),
        }

    def _parse_suggestions(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        raw_entries = data.get("categorySuggestions") or data.get("category_suggestions") or []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                continue
            category = entry.get("category") or {}
            ancestors = entry.get("categoryTreeNodeAncestors") or entry.get("category_tree_node_ancestors") or []
            path_segments: list[str] = []
            for ancestor in ancestors:
                if not isinstance(ancestor, dict):
                    continue
                ancestor_category = ancestor.get("category") or {}
                name = ancestor_category.get("categoryName")
                if name:
                    path_segments.append(name)
            path_segments.append(category.get("categoryName"))
            suggestion = self._build_entry(category, path_segments, True)
            if suggestion is not None:
                suggestions.append(suggestion)
        return suggestions

