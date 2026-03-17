from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.feeds.renderer import MiraklProductFeedFileFactory
from sales_channels.integrations.mirakl.factories.feeds.submit import MiraklProductFeedSubmitFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed, MiraklSalesChannelFeedItem


class MiraklProductFeedFactory:
    """Close gathering Mirakl feeds, render their CSV, and submit them."""

    gather_window = timedelta(minutes=20)

    def __init__(
        self,
        *,
        sales_channel,
        force_full: bool = False,
    ) -> None:
        self.sales_channel = sales_channel
        self.force_full = force_full

    def run(self) -> MiraklSalesChannelFeed | None:
        processed_feeds = self.run_all()
        return processed_feeds[-1] if processed_feeds else None

    def run_all(self) -> list[MiraklSalesChannelFeed]:
        processed_feeds: list[MiraklSalesChannelFeed] = []
        for feed in self._get_candidate_feeds():
            processed_feed = self._process_feed(feed=feed)
            if processed_feed is not None:
                processed_feeds.append(processed_feed)
        return processed_feeds

    def _get_candidate_feeds(self):
        queryset = (
            MiraklSalesChannelFeed.objects.filter(
                sales_channel=self.sales_channel,
                type=MiraklSalesChannelFeed.TYPE_PRODUCT,
                stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
                status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
            )
            .select_related("product_type", "sales_channel_view")
            .order_by("created_at")
        )
        if not self.force_full:
            cutoff = timezone.now() - self.gather_window
            queryset = queryset.filter(updated_at__lte=cutoff)
        return queryset

    def _process_feed(self, *, feed: MiraklSalesChannelFeed) -> MiraklSalesChannelFeed | None:
        feed = self._lock_feed_for_processing(feed=feed)
        if feed is None:
            return None

        self._persist_feed_payload(feed=feed)
        if not self._feed_has_rows(feed=feed):
            self._delete_empty_feed(feed=feed)
            return None

        self._render_feed_file(feed=feed)
        self._submit_feed_if_possible(feed=feed)
        return feed

    def _lock_feed_for_processing(self, *, feed: MiraklSalesChannelFeed) -> MiraklSalesChannelFeed | None:
        with transaction.atomic():
            locked_feed = (
                MiraklSalesChannelFeed.objects.select_for_update()
                .get(id=feed.id)
            )
            if locked_feed.status != MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS:
                return None
            if self._has_pending_feed_for_group(feed=locked_feed):
                return None
            locked_feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
            locked_feed.save(update_fields=["status", "updated_at"])
            return locked_feed

    def _has_pending_feed_for_group(self, *, feed: MiraklSalesChannelFeed) -> bool:
        return MiraklSalesChannelFeed.objects.filter(
            sales_channel_id=feed.sales_channel_id,
            product_type_id=feed.product_type_id,
            sales_channel_view_id=feed.sales_channel_view_id,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            status__in=[
                MiraklSalesChannelFeed.STATUS_PENDING,
                MiraklSalesChannelFeed.STATUS_SUBMITTED,
                MiraklSalesChannelFeed.STATUS_PROCESSING,
            ],
        ).exclude(id=feed.id).exists()

    def _persist_feed_payload(self, *, feed: MiraklSalesChannelFeed) -> None:
        payload_data: list[dict[str, str]] = []
        items_count = 0
        for item in self._get_feed_items(feed=feed):
            items_count += 1
            payload_data.extend(item.payload_data or [])

        feed.payload_data = payload_data
        feed.items_count = items_count
        feed.rows_count = len(payload_data)
        feed.save(update_fields=["payload_data", "items_count", "rows_count"])

    def _get_feed_items(self, *, feed: MiraklSalesChannelFeed):
        queryset = MiraklSalesChannelFeedItem.objects.filter(feed=feed).select_related(
            "remote_product",
            "remote_product__local_instance",
            "sales_channel_view",
        ).order_by("id")
        return queryset

    def _feed_has_rows(self, *, feed: MiraklSalesChannelFeed) -> bool:
        return bool(feed.payload_data)

    def _delete_empty_feed(self, *, feed: MiraklSalesChannelFeed) -> None:
        feed.delete()

    def _render_feed_file(self, *, feed: MiraklSalesChannelFeed) -> None:
        MiraklProductFeedFileFactory(feed=feed).run()

    def _submit_feed_if_possible(self, *, feed: MiraklSalesChannelFeed) -> None:
        if not self.sales_channel.connected:
            return
        MiraklProductFeedSubmitFactory(feed=feed).run()


MiraklProductFeedBuildFactory = MiraklProductFeedFactory
