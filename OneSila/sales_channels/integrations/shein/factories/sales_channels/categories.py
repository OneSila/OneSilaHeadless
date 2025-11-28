"""Factory that queries Shein for category suggestions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db.models import QuerySet

from media.models import Image

from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinSalesChannel,
    SheinSalesChannelView,
)


class SheinCategorySuggestionFactory(SheinSignatureMixin):
    """Call the Shein image-category-suggestion endpoint and normalise the response."""

    suggestion_path = "/open-api/goods/image-category-suggestion"

    def __init__(
        self,
        *,
        view: Any,
        query: Optional[str] = None,
        image_url: Optional[str] = None,
        image: Optional[Image] = None,
    ) -> None:
        self.original_view = view
        self.view = self._resolve_view(view)
        self.sales_channel = self._resolve_sales_channel(self.view, view)
        self.query = (query or "").strip()
        self.explicit_image_url = (image_url or "").strip()
        self.image = image
        self.site_remote_id = self._resolve_site_remote_id()
        self.categories: List[Dict[str, Any]] = []
        self._raw_payload: Dict[str, Any] = {}
        self._normalized_payload: Dict[str, Any] = {}
        self._category_cache: dict[str, Optional[SheinCategory]] = {}

    def run(self) -> None:
        self._reset_state()
        if not self._resolve_context():
            return
        payload = self._build_payload()
        if payload is None:
            return
        self._fetch_payload(payload=payload)
        self._normalize_payload()
        self.categories = self._parse_suggestions()

    def _reset_state(self) -> None:
        self.categories = []
        self._raw_payload = {}
        self._normalized_payload = {}
        self._category_cache = {}

    def _resolve_context(self) -> bool:
        return self.view is not None and self.sales_channel is not None

    def _build_payload(self) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        if self.query:
            payload["productInfo"] = self.query
        image_url = self._resolve_image_url()
        if image_url:
            payload["url"] = image_url
        if not payload:
            return None
        return payload

    def _resolve_image_url(self) -> str:
        if self.explicit_image_url:
            return self.explicit_image_url
        if not self.image:
            return ""
        getter = getattr(self.image, "image_url", None)
        if callable(getter):
            value = getter()
            if value:
                return value
        file_field = getattr(self.image, "image", None)
        url = getattr(file_field, "url", None)
        return str(url or "")

    def _fetch_payload(self, *, payload: Dict[str, Any]) -> None:
        try:
            response = self.shein_post(path=self.suggestion_path, payload=payload)
        except ValueError:
            self._raw_payload = {}
            return
        try:
            self._raw_payload = response.json()
        except ValueError:
            self._raw_payload = {}

    def _normalize_payload(self) -> None:
        self._normalized_payload = self._raw_payload if isinstance(self._raw_payload, dict) else {}

    def _parse_suggestions(self) -> List[Dict[str, Any]]:
        normalized = self._normalized_payload
        if normalized.get("code") not in {"0", 0}:
            return []
        info = normalized.get("info") or {}
        records = info.get("data") or []
        suggestions: List[Dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            remote_id = self._normalize_identifier(
                record.get("categoryId") or record.get("category_id"),
            )
            if remote_id is None:
                continue
            suggestion = self._build_entry(
                remote_id=remote_id,
                order=self._safe_int(record.get("order")),
                vote=self._safe_int(record.get("vote")),
            )
            suggestions.append(suggestion)
        return suggestions

    def _build_entry(
        self,
        *,
        remote_id: str,
        order: Optional[int],
        vote: Optional[int],
    ) -> Dict[str, Any]:
        category = self._get_category(remote_id)
        category_name = self._safe_string(getattr(category, "name", ""))
        category_path = self._build_category_path(category)
        leaf = bool(getattr(category, "is_leaf", False))
        product_type_id = self._normalize_identifier(
            getattr(category, "product_type_remote_id", None),
        ) or ""
        return {
            "category_id": remote_id,
            "product_type_id": product_type_id,
            "category_name": category_name,
            "category_path": category_path,
            "leaf": leaf,
            "order": order,
            "vote": vote,
        }

    def _build_category_path(self, category: Optional[SheinCategory]) -> str:
        if category is None:
            return ""
        segments: List[str] = []
        visited: set[str] = set()
        current = category
        while current and current.remote_id not in visited:
            label = current.name or current.remote_id or ""
            if label:
                segments.append(label)
            visited.add(current.remote_id)
            if current.parent:
                current = current.parent
                continue
            parent_remote_id = getattr(current, "parent_remote_id", "") or ""
            if not parent_remote_id:
                break
            current = self._get_category(parent_remote_id)
        return " > ".join(reversed(segments))

    def _resolve_view(self, view: Any) -> Optional[SheinSalesChannelView]:
        if isinstance(view, SheinSalesChannelView):
            return view
        getter = getattr(view, "get_real_instance", None)
        if callable(getter):
            resolved = getter()
            if isinstance(resolved, SheinSalesChannelView):
                return resolved
        pk = getattr(view, "pk", None)
        if pk:
            queryset: QuerySet[SheinSalesChannelView] = SheinSalesChannelView.objects.filter(pk=pk)
            return queryset.select_related("sales_channel").first()
        return None

    def _resolve_sales_channel(
        self,
        resolved_view: Optional[SheinSalesChannelView],
        original_view: Any,
    ) -> Optional[SheinSalesChannel]:
        candidate = getattr(resolved_view, "sales_channel", None) if resolved_view else None
        if candidate is None and original_view is not None:
            candidate = getattr(original_view, "sales_channel", None)
        if isinstance(candidate, SheinSalesChannel):
            return candidate
        getter = getattr(candidate, "get_real_instance", None)
        if callable(getter):
            resolved = getter()
            if isinstance(resolved, SheinSalesChannel):
                return resolved
        pk = getattr(candidate, "pk", None)
        if pk:
            return SheinSalesChannel.objects.filter(pk=pk).first()
        return None

    def _resolve_site_remote_id(self) -> str:
        remote_id = getattr(self.view, "remote_id", None)
        return str(remote_id).strip() if remote_id else ""

    def _get_category(self, remote_id: str) -> Optional[SheinCategory]:
        if remote_id in self._category_cache:
            return self._category_cache[remote_id]
        queryset = SheinCategory.objects.select_related("parent").filter(
            remote_id=remote_id,
            site_remote_id=self.site_remote_id or "",
        )
        category = queryset.first()
        self._category_cache[remote_id] = category
        return category

    @staticmethod
    def _normalize_identifier(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _safe_string(value: Any) -> str:
        return str(value).strip() if isinstance(value, str) else ""

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            if value is None or value == "":
                return None
            return int(value)
        except (TypeError, ValueError):
            return None
