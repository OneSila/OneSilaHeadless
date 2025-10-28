from __future__ import annotations

from sales_channels.factories.gpt.product_feed import SalesChannelGptProductFeedFactory

__all__ = [
    "sync_gpt_feed",
    "remove_from_gpt_feed",
]


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
