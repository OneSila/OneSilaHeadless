from __future__ import annotations

from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklFeedResyncFactory,
)
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed
from sales_channels.models import SalesChannelFeed


def process_mirakl_gathering_product_feeds(
    *,
    sales_channel_id: int | None = None,
) -> list[SalesChannelFeed]:
    queryset = MiraklSalesChannelFeed.objects.filter(
        type=MiraklSalesChannelFeed.TYPE_PRODUCT,
        stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
        status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        sales_channel__active=True,
    ).select_related("sales_channel")
    if sales_channel_id is not None:
        queryset = queryset.filter(sales_channel_id=sales_channel_id)

    processed: list[SalesChannelFeed] = []
    for feed in queryset.order_by("id").iterator():
        if feed.status != MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS:
            continue
        feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
        feed.save(update_fields=["status", "updated_at"])
        processed.append(feed)
    return processed


def resync_mirakl_feed(*, feed_id: int) -> MiraklSalesChannelFeed:
    feed = MiraklSalesChannelFeed.objects.select_related(
        "sales_channel",
        "product_type",
        "sales_channel_view",
    ).get(id=feed_id)
    return MiraklFeedResyncFactory(feed=feed).run()
