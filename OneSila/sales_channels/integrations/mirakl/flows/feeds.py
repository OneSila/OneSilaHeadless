from __future__ import annotations

from django.core.files.base import ContentFile

from sales_channels.integrations.mirakl.factories.feeds import (
    MiraklImportStatusSyncFactory,
    MiraklProductFeedBuildFactory,
)
from sales_channels.integrations.mirakl.models import (
    MiraklSalesChannel,
    MiraklSalesChannelFeed,
    MiraklSalesChannelFeedItem,
)
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


def process_mirakl_gathering_product_feeds(
    *,
    sales_channel_id: int | None = None,
    remote_product_ids: list[int] | None = None,
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
    if remote_product_ids:
        feed_ids = MiraklSalesChannelFeedItem.objects.filter(
            remote_product_id__in=remote_product_ids,
        ).values_list("feed_id", flat=True)
        queryset = queryset.filter(id__in=feed_ids)

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
            remote_product_ids=remote_product_ids,
            force_full=force,
        )
        processed.extend(feed_factory.run_all())
    return processed


def sync_mirakl_product_feeds(
    *,
    sales_channel_id: int | None = None,
    remote_product_ids: list[int] | None = None,
    force: bool = False,
) -> list[SalesChannelFeed]:
    return process_mirakl_gathering_product_feeds(
        sales_channel_id=sales_channel_id,
        remote_product_ids=remote_product_ids,
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
    feed = MiraklSalesChannelFeed.objects.select_related("sales_channel", "product_type", "sales_channel_view").get(id=feed_id)
    retry_feed = feed.__class__.objects.create(
        sales_channel=feed.sales_channel,
        multi_tenant_company=feed.multi_tenant_company,
        type=feed.type,
        status=SalesChannelFeed.STATUS_NEW,
        summary_data=feed.summary_data,
        error_message="",
        stage=getattr(feed, "stage", feed.STAGE_PRODUCT),
        raw_data={},
        product_type=feed.product_type,
        sales_channel_view=feed.sales_channel_view,
    )
    if feed.file:
        with feed.file.open("rb") as file_handle:
            content = file_handle.read()
        retry_feed.file.save(feed.file.name.rsplit("/", 1)[-1], ContentFile(content), save=False)
        retry_feed.save(update_fields=["file"])

    items = []
    for item in MiraklSalesChannelFeedItem.objects.filter(feed=feed).select_related("remote_product").iterator():
        items.append(
            MiraklSalesChannelFeedItem(
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
    MiraklSalesChannelFeedItem.objects.bulk_create(items)

    from sales_channels.integrations.mirakl.factories.feeds import MiraklProductFeedSubmitFactory

    MiraklProductFeedSubmitFactory(feed=retry_feed).run()
    return retry_feed
