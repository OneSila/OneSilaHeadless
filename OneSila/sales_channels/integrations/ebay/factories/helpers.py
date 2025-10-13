"""Shared helpers for eBay factory modules."""

from __future__ import annotations

from typing import Any

from sales_channels.integrations.ebay.models.sales_channels import EbaySalesChannelView


def resolve_ebay_view(view: Any) -> EbaySalesChannelView | None:
    """Return the concrete `EbaySalesChannelView` instance for the provided view-like object."""
    if isinstance(view, EbaySalesChannelView):
        return view
    if view is None:
        return None

    getter = getattr(view, "get_real_instance", None)
    if callable(getter):
        real_view = getter()
        if isinstance(real_view, EbaySalesChannelView):
            return real_view

    pk = getattr(view, "pk", None)
    if pk is None:
        return None

    return EbaySalesChannelView.objects.filter(pk=pk).first()


def normalize_ebay_response(value: Any) -> Any:
    """Convert API responses into JSON-serializable primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {key: normalize_ebay_response(val) for key, val in value.items()}

    if isinstance(value, (list, tuple)):
        return [normalize_ebay_response(item) for item in value]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:  # pragma: no cover - defensive
            return str(value)

    return str(value)
