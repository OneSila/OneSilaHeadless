from __future__ import annotations

from django.core.files.base import ContentFile

from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklImportStatusSyncFactory,
    MiraklOfferSubmitFactory,
    MiraklProductFeedBuildFactory,
    mark_remote_products_for_mirakl_feed_updates,
)
from sales_channels.integrations.mirakl.models import (
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
)
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


def process_mirakl_gathering_product_feeds(*, sales_channel_id: int | None = None, force: bool = False) -> list[SalesChannelFeed]:
    queryset = MiraklSalesChannelFeed.objects.filter(
        type=MiraklSalesChannelFeed.TYPE_PRODUCT,
        stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
        status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        sales_channel__active=True,
    ).select_related("sales_channel")
    if sales_channel_id is not None:
        queryset = queryset.filter(sales_channel_id=sales_channel_id)

    processed_feeds: list[SalesChannelFeed] = []
    processed_channel_ids: set[int] = set()
    for gathering_feed in queryset.order_by("created_at").iterator():
        sales_channel = gathering_feed.sales_channel
        if sales_channel.id in processed_channel_ids:
            continue
        processed_channel_ids.add(sales_channel.id)

        if not sales_channel.connected:
            continue
        if SalesChannelFeed.objects.filter(
            sales_channel=sales_channel,
            type=SalesChannelFeed.TYPE_PRODUCT,
            status__in=[
                SalesChannelFeed.STATUS_PENDING,
                SalesChannelFeed.STATUS_SUBMITTED,
                SalesChannelFeed.STATUS_PROCESSING,
            ],
        ).exists():
            continue
        feed = MiraklProductFeedBuildFactory(sales_channel=sales_channel, force_full=force).run()
        if feed is None:
            continue
        processed_feeds.append(feed)
    return processed_feeds


def sync_mirakl_product_feeds(*, sales_channel_id: int | None = None, force: bool = False) -> list[SalesChannelFeed]:
    """Backward-compatible alias; the real source of truth is gathering feeds."""
    return process_mirakl_gathering_product_feeds(
        sales_channel_id=sales_channel_id,
        force=force,
    )


def refresh_mirakl_feed_statuses(*, feed_id: int | None = None, sales_channel_id: int | None = None) -> list[MiraklSalesChannelFeed]:
    queryset = MiraklSalesChannelFeed.objects.filter(
        sales_channel__active=True,
        remote_id__gt="",
        status__in=[
            SalesChannelFeed.STATUS_PENDING,
            SalesChannelFeed.STATUS_SUBMITTED,
            SalesChannelFeed.STATUS_PROCESSING,
        ],
    )
    if feed_id is not None:
        queryset = queryset.filter(id=feed_id)
    if sales_channel_id is not None:
        queryset = queryset.filter(sales_channel_id=sales_channel_id)

    refreshed: list[MiraklSalesChannelFeed] = []
    for feed in queryset.select_related("sales_channel").iterator():
        refreshed.append(MiraklImportStatusSyncFactory(feed=feed).run())
    return refreshed


def refresh_mirakl_imports(*, import_process_id: int | None = None, sales_channel_id: int | None = None):
    from sales_channels.integrations.mirakl.models import MiraklSalesChannelImport

    queryset = MiraklSalesChannelImport.objects.all()
    if import_process_id is not None:
        queryset = queryset.filter(id=import_process_id)
    if sales_channel_id is not None:
        queryset = queryset.filter(sales_channel_id=sales_channel_id)
    return list(queryset)


def retry_mirakl_feed(*, feed_id: int) -> SalesChannelFeed:
    feed = SalesChannelFeed.objects.select_related("sales_channel").get(id=feed_id)
    raw_data = dict(getattr(feed, "raw_data", {}) or {})
    if raw_data.get("product_import_succeeded") and not raw_data.get("offer_import_succeeded"):
        from sales_channels.integrations.mirakl.factories.feeds import MiraklOfferPayloadFactory

        MiraklOfferSubmitFactory(feed=feed, offers=MiraklOfferPayloadFactory(feed=feed).build()).run()
        return feed

    retry_feed = feed.__class__.objects.create(
        sales_channel=feed.sales_channel,
        multi_tenant_company=feed.multi_tenant_company,
        type=feed.type,
        status=SalesChannelFeed.STATUS_NEW,
        summary_data=feed.summary_data,
        error_message="",
        stage=getattr(feed, "stage", "product"),
        raw_data=getattr(feed, "raw_data", {}),
    )
    if feed.file:
        with feed.file.open("rb") as file_handle:
            content = file_handle.read()
        retry_feed.file.save(feed.file.name.rsplit("/", 1)[-1], ContentFile(content), save=False)
        retry_feed.save(update_fields=["file"])

    items = []
    for item in feed.items.select_related("remote_product").iterator():
        items.append(
            SalesChannelFeedItem(
                feed=retry_feed,
                multi_tenant_company=retry_feed.multi_tenant_company,
                remote_product=item.remote_product,
                sales_channel_view=item.sales_channel_view,
                action=item.action,
                status=SalesChannelFeedItem.STATUS_PENDING,
                identifier=item.identifier,
                payload_data=item.payload_data,
                result_data={},
            )
        )
    SalesChannelFeedItem.objects.bulk_create(items)
    from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedSubmitFactory

    MiraklProductFeedSubmitFactory(feed=retry_feed).run()
    return retry_feed


def mark_product_property_for_mirakl_feed_update(*, product_property) -> None:
    product = getattr(product_property, "product", None)
    if product is None:
        return
    mark_remote_products_for_mirakl_feed_updates(product_ids=[product.id])
