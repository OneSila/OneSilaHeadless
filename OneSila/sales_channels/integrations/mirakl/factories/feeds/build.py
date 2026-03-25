from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.feeds.renderer import MiraklProductFeedFileFactory
from sales_channels.integrations.mirakl.factories.feeds.submit import MiraklProductFeedSubmitFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed, MiraklSalesChannelFeedItem


class MiraklProductFeedFactory:
    """Process one Mirakl feed already marked ready_to_render."""

    def __init__(self, *, feed: MiraklSalesChannelFeed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel.get_real_instance()

    def run(self) -> MiraklSalesChannelFeed | None:
        feed = self._claim_feed_for_processing(feed=self.feed)
        if feed is None:
            return None

        try:
            self._persist_feed_payload(feed=feed)
            if not self._feed_has_rows(feed=feed):
                self._delete_empty_feed(feed=feed)
                return None

            self._render_feed_file(feed=feed)
            self._submit_feed_if_possible(feed=feed)
            return feed
        except Exception as exc:
            self._reset_feed_to_ready(feed=feed, error_message=str(exc))
            raise

    def _claim_feed_for_processing(self, *, feed: MiraklSalesChannelFeed) -> MiraklSalesChannelFeed | None:
        with transaction.atomic():
            locked_feed = (
                MiraklSalesChannelFeed.objects.select_for_update()
                .get(id=feed.id)
            )
            if locked_feed.status != MiraklSalesChannelFeed.STATUS_READY_TO_RENDER:
                return None
            if self._has_pending_feed_for_group(feed=locked_feed):
                locked_feed.status = MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS
                locked_feed.save(update_fields=["status", "updated_at"])
                return None
            locked_feed.status = MiraklSalesChannelFeed.STATUS_PROCESSING
            locked_feed.error_message = ""
            locked_feed.save(update_fields=["status", "error_message", "updated_at"])
            return locked_feed

    def _has_pending_feed_for_group(self, *, feed: MiraklSalesChannelFeed) -> bool:
        return MiraklSalesChannelFeed.objects.filter(
            sales_channel_id=feed.sales_channel_id,
            product_type_id=feed.product_type_id,
            sales_channel_view_id=feed.sales_channel_view_id,
            type=MiraklSalesChannelFeed.TYPE_COMBINED,
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
            self._reset_feed_to_ready(feed=feed)
            return
        MiraklProductFeedSubmitFactory(feed=feed).run()

    def _reset_feed_to_ready(self, *, feed: MiraklSalesChannelFeed, error_message: str = "") -> None:
        MiraklSalesChannelFeed.objects.filter(
            id=feed.id,
            status=MiraklSalesChannelFeed.STATUS_PROCESSING,
        ).update(
            status=MiraklSalesChannelFeed.STATUS_READY_TO_RENDER,
            error_message=error_message,
            updated_at=timezone.now(),
        )
        feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
        feed.error_message = error_message


MiraklProductFeedBuildFactory = MiraklProductFeedFactory
