from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sales_channels.models.sales_channels import SalesChannelViewAssign


def get_mirakl_remote_url(assign: "SalesChannelViewAssign") -> str | None:
    """Return a storefront URL for the Mirakl tracking if we know a template."""

    try:
        from sales_channels.integrations.mirakl.models import MiraklSalesChannel
    except ImportError:  # pragma: no cover - defensive
        return None

    sales_channel = assign.sales_channel.get_real_instance()
    if not isinstance(sales_channel, MiraklSalesChannel):
        return None

    hostname = (sales_channel.hostname or "").lower()
    if "debenhams" in hostname:
        sku = (assign.product.sku or "").strip()
        if not sku:
            return None
        return f"https://www.debenhams.com/search?text={sku}"

    return None
