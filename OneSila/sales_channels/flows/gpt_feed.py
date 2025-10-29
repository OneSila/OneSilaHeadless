from __future__ import annotations

from django.db.models import Q

from llm.models import ChatGptProductFeedConfig
from properties.models import ProductProperty, Property

from sales_channels.factories.gpt.product_feed import SalesChannelGptProductFeedFactory
from sales_channels.helpers import mark_remote_products_for_feed_updates

__all__ = [
    "sync_gpt_feed",
    "remove_from_gpt_feed",
    "mark_product_property_for_gpt_feed_update",
]


GPT_CONFIG_PROPERTY_FIELD_NAMES = tuple(
    field.name
    for field in ChatGptProductFeedConfig._meta.get_fields()
    if getattr(field, "related_model", None) is Property and getattr(field, "many_to_one", False)
)


def sync_gpt_feed(*, sales_channel_id: int | None = None, sync_all: bool = False) -> None:
    SalesChannelGptProductFeedFactory(
        sync_all=sync_all,
        sales_channel_id=sales_channel_id,
    ).run()


def remove_from_gpt_feed(*, sales_channel_id: int, sku: str) -> None:
    SalesChannelGptProductFeedFactory(
        sync_all=False,
        sales_channel_id=sales_channel_id,
        deleted_sku=sku,
    ).run()


def mark_product_property_for_gpt_feed_update(*, product_property: ProductProperty) -> None:
    property_id = getattr(product_property, "property_id", None)
    company_id = getattr(product_property, "multi_tenant_company_id", None)
    if not property_id or not company_id:
        return

    property_filters = Q()
    for field_name in GPT_CONFIG_PROPERTY_FIELD_NAMES:
        property_filters |= Q(**{f"{field_name}_id": property_id})

    if not property_filters:
        return

    is_relevant = ChatGptProductFeedConfig.objects.filter(
        multi_tenant_company_id=company_id,
    ).filter(property_filters).exists()

    if not is_relevant:
        return

    mark_remote_products_for_feed_updates(
        product_ids=[getattr(product_property, "product_id", None)]
    )
