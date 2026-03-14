from __future__ import annotations

from collections import OrderedDict

from django.core.exceptions import ValidationError

from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertyApplicability,
    MiraklSalesChannelView,
)


def get_mirakl_category_header_properties(*, sales_channel, sales_channel_view, category_remote_id: str) -> list[MiraklProperty]:
    if not category_remote_id:
        raise ValidationError("Mirakl product category is missing.")

    resolved_view = _resolve_sales_channel_view(sales_channel_view=sales_channel_view)
    category = MiraklCategory.objects.select_related("parent").get(
        sales_channel=sales_channel,
        remote_id=category_remote_id,
    )

    applicable_property_ids = set(
        MiraklPropertyApplicability.objects.filter(
            sales_channel=sales_channel,
            view=resolved_view,
        ).values_list("property_id", flat=True)
    )

    ordered_properties: OrderedDict[str, MiraklProperty] = OrderedDict()

    common_properties = (
        MiraklProperty.objects.filter(
            sales_channel=sales_channel,
            is_common=True,
            id__in=applicable_property_ids,
        )
        .exclude(requirement_level="DISABLED")
        .order_by("code")
    )
    for remote_property in common_properties:
        code = str(remote_property.code or "").strip()
        if code:
            ordered_properties.setdefault(code, remote_property)

    for chain_category in _get_category_chain(category=category):
        product_type = (
            MiraklProductType.objects.filter(
                sales_channel=sales_channel,
                category=chain_category,
            )
            .select_related("category")
            .first()
        )
        if product_type is None:
            continue

        items = (
            MiraklProductTypeItem.objects.filter(
                product_type=product_type,
                remote_property_id__in=applicable_property_ids,
            )
            .exclude(remote_property__requirement_level="DISABLED")
            .select_related("remote_property")
            .order_by("id")
        )
        for item in items:
            code = str(item.remote_property.code or "").strip()
            if code:
                ordered_properties.setdefault(code, item.remote_property)

    return list(ordered_properties.values())


def get_mirakl_category_headers(*, sales_channel, sales_channel_view, category_remote_id: str) -> list[str]:
    return [
        remote_property.code
        for remote_property in get_mirakl_category_header_properties(
            sales_channel=sales_channel,
            sales_channel_view=sales_channel_view,
            category_remote_id=category_remote_id,
        )
        if str(remote_property.code or "").strip()
    ]


def _resolve_sales_channel_view(*, sales_channel_view):
    if isinstance(sales_channel_view, MiraklSalesChannelView):
        return sales_channel_view
    if hasattr(sales_channel_view, "get") and hasattr(sales_channel_view, "model"):
        return sales_channel_view.get()
    return MiraklSalesChannelView.objects.get(id=sales_channel_view)


def _get_category_chain(*, category: MiraklCategory) -> list[MiraklCategory]:
    chain: list[MiraklCategory] = []
    current = category
    while current is not None:
        chain.append(current)
        current = current.parent
    chain.reverse()
    return chain
