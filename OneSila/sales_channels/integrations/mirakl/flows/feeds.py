from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklFeedResyncFactory,
    MiraklImportStatusSyncFactory,
    MiraklProductFeedBuildFactory,
)
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelFeed
from sales_channels.models import SalesChannelFeed


def process_mirakl_gathering_product_feeds(
    *,
    sales_channel_id: int | None = None,
    force: bool = False,
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
    processed_channel_ids: set[int] = set()
    for sales_channel_id_value in queryset.order_by("sales_channel_id").values_list("sales_channel_id", flat=True).distinct():
        if sales_channel_id_value in processed_channel_ids:
            continue
        processed_channel_ids.add(sales_channel_id_value)

        sales_channel = MiraklSalesChannel.objects.filter(id=sales_channel_id_value).first()
        if sales_channel is None:
            continue

        feed_factory = MiraklProductFeedBuildFactory(
            sales_channel=sales_channel,
            force_full=force,
        )
        processed.extend(feed_factory.run_all())
    return processed


def sync_mirakl_product_feeds(
    *,
    sales_channel_id: int | None = None,
    force: bool = False,
) -> list[SalesChannelFeed]:
    return process_mirakl_gathering_product_feeds(
        sales_channel_id=sales_channel_id,
        force=force,
    )


def sync_mirakl_product_import_statuses(*, sales_channel_id: int | None = None) -> list[MiraklSalesChannelFeed]:
    queryset = MiraklSalesChannel.objects.filter(active=True)
    if sales_channel_id is not None:
        queryset = queryset.filter(id=sales_channel_id)
    else:
        cutoff = timezone.now() - timedelta(minutes=15)
        queryset = queryset.filter(
            Q(last_product_imports_request_date__isnull=True)
            | Q(last_product_imports_request_date__lt=cutoff)
        )

    refreshed: list[MiraklSalesChannelFeed] = []
    for sales_channel in queryset.order_by("id").iterator():
        refreshed.extend(
            MiraklImportStatusSyncFactory(
                sales_channel=sales_channel,
            ).run()
        )
    return refreshed


def resync_mirakl_feed(*, feed_id: int) -> MiraklSalesChannelFeed:
    feed = MiraklSalesChannelFeed.objects.select_related(
        "sales_channel",
        "product_type",
        "sales_channel_view",
    ).get(id=feed_id)
    return MiraklFeedResyncFactory(feed=feed).run()
