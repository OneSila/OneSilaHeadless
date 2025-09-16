"""Factories for building eBay product type rules."""

from __future__ import annotations

from typing import Optional

from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelView


class EbayProductTypeRuleFactory(GetEbayAPIMixin):
    """Placeholder factory that will build local rules for eBay product types."""

    def __init__(
        self,
        *,
        sales_channel: EbaySalesChannel,
        view: EbaySalesChannelView,
        category_id: str,
        category_tree_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        self.sales_channel = sales_channel
        self.view = self._ensure_real_view(view)
        self.category_id = str(category_id) if category_id is not None else None
        self.category_tree_id = category_tree_id or getattr(self.view, "default_category_tree_id", None)
        self.language = language

        # Each factory instance needs its own API configured for the specific view headers.
        self.api = self.get_api()

    def run(self) -> None:
        """Build local product type rules for the configured category."""

        # Implementation will be provided in a follow-up iteration.
        return None

    @staticmethod
    def _ensure_real_view(view: EbaySalesChannelView) -> EbaySalesChannelView:
        """Return the concrete EbaySalesChannelView instance for polymorphic wrappers."""

        real_view_getter = getattr(view, "get_real_instance", None)
        if callable(real_view_getter):
            real_view = real_view_getter()
            if isinstance(real_view, EbaySalesChannelView):
                return real_view
        return view
