from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from sales_channels.integrations.mirakl.factories.feeds.product_payloads import MiraklProductPayloadBuilder
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed, MiraklSalesChannelFeedItem
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


class MiraklFeedResyncFactory:
    """Create a new Mirakl feed by regenerating payloads for a concluded submitted artifact."""

    def __init__(self, *, feed: MiraklSalesChannelFeed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel

    def run(self) -> MiraklSalesChannelFeed:
        self._validate_source_feed()
        resynced_feed = self._create_feed()
        try:
            self._populate_feed(feed=resynced_feed)
        except Exception:
            resynced_feed.delete()
            raise
        return resynced_feed

    def _validate_source_feed(self) -> None:
        if self.feed.status not in SalesChannelFeed.CONCLUDED_STATUSES:
            raise ValidationError("Only concluded Mirakl feeds can be resynced.")
        if self.feed.type != MiraklSalesChannelFeed.TYPE_PRODUCT:
            raise ValidationError("Only Mirakl product feeds can be resynced.")

    def _create_feed(self) -> MiraklSalesChannelFeed:
        return MiraklSalesChannelFeed.objects.create(
            sales_channel=self.feed.sales_channel,
            multi_tenant_company=self.feed.multi_tenant_company,
            type=self.feed.type,
            status=SalesChannelFeed.STATUS_NEW,
            error_message="",
            stage=getattr(self.feed, "stage", MiraklSalesChannelFeed.STAGE_PRODUCT),
            raw_data={},
            payload_data=[],
            product_type=self.feed.product_type,
            sales_channel_view=self.feed.sales_channel_view,
            import_status="",
            reason_status="",
            product_remote_id="",
            offer_remote_id="",
            offer_import_remote_id="",
            remote_id="",
        )

    def _populate_feed(self, *, feed: MiraklSalesChannelFeed) -> None:
        source_items = list(
            MiraklSalesChannelFeedItem.objects.filter(feed=self.feed)
            .select_related("remote_product", "remote_product__local_instance", "sales_channel_view")
            .order_by("id")
        )
        if not source_items:
            raise ValidationError("The selected Mirakl feed has no items to resync.")

        payload_data: list[dict] = []
        resynced_items: list[MiraklSalesChannelFeedItem] = []
        for source_item in source_items:
            product_type, rows = MiraklProductPayloadBuilder(
                remote_product=source_item.remote_product,
                sales_channel_view=source_item.sales_channel_view,
                action=source_item.action,
            ).build()
            if self.feed.product_type_id and product_type.id != self.feed.product_type_id:
                raise ValidationError("Mirakl feed resync produced a different product type than the original feed.")

            payload_data.extend(rows)
            resynced_items.append(
                MiraklSalesChannelFeedItem(
                    feed=feed,
                    multi_tenant_company=feed.multi_tenant_company,
                    remote_product=source_item.remote_product,
                    sales_channel_view=source_item.sales_channel_view,
                    action=source_item.action,
                    status=SalesChannelFeedItem.STATUS_PENDING,
                    identifier=source_item.identifier,
                    payload_data=rows,
                    result_data={},
                    error_message="",
                )
            )

        if not payload_data:
            raise ValidationError("Mirakl feed resync did not generate any rows.")

        with transaction.atomic():
            for item in resynced_items:
                item.save()
            feed.payload_data = payload_data
            feed.items_count = len(resynced_items)
            feed.rows_count = len(payload_data)
            feed.status = MiraklSalesChannelFeed.STATUS_READY_TO_RENDER
            feed.save(update_fields=["payload_data", "items_count", "rows_count", "status", "updated_at"])
