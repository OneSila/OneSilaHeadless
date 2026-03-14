from __future__ import annotations

from sales_channels.integrations.mirakl.factories.feeds.payloads import (
    MiraklProductCreateFactory,
    MiraklProductDeleteFactory,
    MiraklProductUpdateFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklProduct,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


def mark_remote_products_for_mirakl_feed_updates(*, product_ids: list[int]) -> None:
    valid_product_ids = [product_id for product_id in product_ids if product_id]
    if not valid_product_ids:
        return

    assignments = (
        SalesChannelViewAssign.objects.filter(
            product_id__in=valid_product_ids,
            sales_channel_view_id__in=MiraklSalesChannelView.objects.values_list("id", flat=True),
        )
        .select_related("product", "sales_channel_view", "remote_product", "sales_channel_view__sales_channel")
        .order_by("id")
    )

    processed_remote_products: set[tuple[int, int, int]] = set()
    for assignment in assignments.iterator():
        view = assignment.sales_channel_view
        sales_channel = getattr(view, "sales_channel", None)
        product = assignment.product
        if sales_channel is None or product is None:
            continue

        remote_product = _get_or_create_remote_product(sales_channel=sales_channel, product=product)

        if assignment.remote_product_id != remote_product.id:
            assignment.remote_product = remote_product
            assignment.save(update_fields=["remote_product"])

        processed_key = (sales_channel.id, remote_product.id, view.id)
        if processed_key in processed_remote_products:
            continue
        processed_remote_products.add(processed_key)

        _get_sync_factory(remote_product=remote_product, sales_channel_view=view).run()


def _get_or_create_remote_product(*, sales_channel, product):
    remote_product, _created = MiraklProduct.objects.get_or_create(
        sales_channel=sales_channel,
        multi_tenant_company=sales_channel.multi_tenant_company,
        local_instance=product,
        remote_parent_product=None,
        remote_sku=getattr(product, "sku", "") or "",
    )
    return remote_product


def _get_sync_factory(*, remote_product, sales_channel_view):
    product = remote_product.local_instance
    if product is None or not product.active:
        return MiraklProductDeleteFactory(remote_product=remote_product, sales_channel_view=sales_channel_view)
    if getattr(remote_product, "remote_id", None) or getattr(remote_product, "product_reference", ""):
        return MiraklProductUpdateFactory(remote_product=remote_product, sales_channel_view=sales_channel_view)
    return MiraklProductCreateFactory(remote_product=remote_product, sales_channel_view=sales_channel_view)
