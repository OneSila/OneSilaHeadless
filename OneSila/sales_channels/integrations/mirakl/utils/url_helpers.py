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
        remote_product = getattr(assign, "remote_product", None)
        sku = ""
        product = getattr(assign, "product", None)
        if product is not None and hasattr(product, "is_configurable") and product.is_configurable():
            try:
                from sales_channels.integrations.mirakl.models import MiraklProduct
            except ImportError:  # pragma: no cover - defensive
                MiraklProduct = None

            if MiraklProduct is not None and remote_product is not None:
                first_variation = (
                    MiraklProduct.objects.filter(
                        sales_channel=sales_channel,
                        remote_parent_product=remote_product,
                    )
                    .select_related("local_instance")
                    .order_by("local_instance__sku", "id")
                    .first()
                )
                sku = str(getattr(first_variation, "remote_sku", "") or "").strip()
        if not sku:
            sku = str(getattr(remote_product, "remote_sku", "") or "").strip()
        if not sku:
            sku = str(getattr(product, "sku", "") or "").strip()
        if not sku:
            return None
        return f"https://www.debenhams.com/search?text={sku}"

    return None
