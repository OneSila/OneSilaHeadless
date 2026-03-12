from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.feeds.renderer import MiraklProductFeedFileFactory
from sales_channels.integrations.mirakl.factories.feeds.submit import MiraklProductFeedSubmitFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed


class MiraklProductFeedFactory:
    """Close a gathering Mirakl product feed and submit it."""

    gather_window = timedelta(minutes=20)

    def __init__(self, *, sales_channel, remote_product_ids: Iterable[int] | None = None, force_full: bool = False) -> None:
        self.sales_channel = sales_channel
        self.remote_product_ids = [remote_product_id for remote_product_id in (remote_product_ids or []) if remote_product_id]
        self.force_full = force_full

    def run(self):
        feed = self._get_gathering_feed()
        if feed is None:
            return None

        feed = self._lock_feed_for_processing(feed=feed)
        if feed is None:
            return None

        self._persist_feed_payload(feed=feed)
        if not self._feed_has_items(feed=feed):
            self._delete_empty_feed(feed=feed)
            return None

        self._render_feed_file(feed=feed)
        self._submit_feed_if_possible(feed=feed)
        return feed

    def _get_gathering_feed(self):
        queryset = MiraklSalesChannelFeed.objects.filter(
            sales_channel=self.sales_channel,
            type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            stage=MiraklSalesChannelFeed.STAGE_PRODUCT,
            status=MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS,
        ).order_by("created_at")
        if not self.force_full:
            cutoff = timezone.now() - self.gather_window
            queryset = queryset.filter(updated_at__lte=cutoff)
        if self.remote_product_ids:
            queryset = queryset.filter(items__remote_product_id__in=self.remote_product_ids).distinct()
        return queryset.first()

    def _lock_feed_for_processing(self, *, feed):
        with transaction.atomic():
            locked_feed = MiraklSalesChannelFeed.objects.select_for_update().get(id=feed.id)
            if locked_feed.status != MiraklSalesChannelFeed.STATUS_GATHERING_PRODUCTS:
                return None
            locked_feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
            locked_feed.save(update_fields=["status", "updated_at"])
            return locked_feed

    def _persist_feed_payload(self, *, feed) -> None:
        payload_data = self._build_payload_data(feed=feed)
        feed.payload_data = payload_data
        feed.summary_data = self._build_summary_data(feed=feed, payload_data=payload_data)
        feed.save(update_fields=["payload_data", "summary_data"])

    def _build_payload_data(self, *, feed) -> list[dict]:
        payload_data = []
        for item in self._get_feed_items(feed=feed):
            payload_data.extend(item.payload_data.get("rows") or [])
        return payload_data

    def _build_summary_data(self, *, feed, payload_data: list[dict]) -> dict[str, int]:
        return {
            "items_count": feed.items.count(),
            "rows_count": len(payload_data),
        }

    def _get_feed_items(self, *, feed):
        queryset = feed.items.select_related("remote_product", "remote_product__local_instance").all()
        if self.remote_product_ids:
            queryset = queryset.filter(remote_product_id__in=self.remote_product_ids)
        return queryset

    def _feed_has_items(self, *, feed) -> bool:
        return feed.items.exists()

    def _delete_empty_feed(self, *, feed) -> None:
        feed.delete()

    def _render_feed_file(self, *, feed) -> None:
        MiraklProductFeedFileFactory(feed=feed).run()

    def _submit_feed_if_possible(self, *, feed) -> None:
        if not self.sales_channel.connected:
            return
        MiraklProductFeedSubmitFactory(feed=feed).run()


MiraklProductFeedBuildFactory = MiraklProductFeedFactory
