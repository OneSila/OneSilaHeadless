from __future__ import annotations

from django.db import transaction

from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


class SalesChannelFeedGatheringFactory:
    """Shared helper for feed integrations that gather product payloads into an open batch."""

    def __init__(
        self,
        *,
        sales_channel,
        feed_model_class=SalesChannelFeed,
        feed_type: str,
        feed_defaults: dict | None = None,
    ) -> None:
        self.sales_channel = sales_channel
        self.feed_model_class = feed_model_class
        self.feed_type = feed_type
        self.feed_defaults = dict(feed_defaults or {})

    def get_or_create_feed(self):
        status = self.feed_model_class.get_gathering_status_for_type(feed_type=self.feed_type)
        with transaction.atomic():
            feed = (
                self.feed_model_class.objects.select_for_update()
                .filter(
                    sales_channel=self.sales_channel,
                    type=self.feed_type,
                    status=status,
                )
                .order_by("-updated_at")
                .first()
            )
            if feed is not None:
                return feed

            return self.feed_model_class.objects.create(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                type=self.feed_type,
                status=status,
                **self.feed_defaults,
            )

    def upsert_item(
        self,
        *,
        remote_product,
        action: str,
        payload_data: dict,
        identifier: str = "",
        sales_channel_view=None,
    ):
        feed = self.get_or_create_feed()
        item, _created = SalesChannelFeedItem.objects.update_or_create(
            feed=feed,
            remote_product=remote_product,
            sales_channel_view=sales_channel_view,
            defaults={
                "multi_tenant_company": self.sales_channel.multi_tenant_company,
                "action": self._merge_action(existing_item=None, new_action=action, existing_feed=feed, remote_product=remote_product, sales_channel_view=sales_channel_view),
                "identifier": identifier,
                "payload_data": payload_data,
                "status": SalesChannelFeedItem.STATUS_PENDING,
                "result_data": {},
                "error_message": "",
            },
        )
        if item.pk:
            merged_action = self._merge_action(
                existing_item=item,
                new_action=action,
                existing_feed=feed,
                remote_product=remote_product,
                sales_channel_view=sales_channel_view,
            )
            changed_fields = []
            if item.action != merged_action:
                item.action = merged_action
                changed_fields.append("action")
            if item.identifier != identifier:
                item.identifier = identifier
                changed_fields.append("identifier")
            if item.payload_data != payload_data:
                item.payload_data = payload_data
                changed_fields.append("payload_data")
            if item.status != SalesChannelFeedItem.STATUS_PENDING:
                item.status = SalesChannelFeedItem.STATUS_PENDING
                changed_fields.append("status")
            if item.result_data:
                item.result_data = {}
                changed_fields.append("result_data")
            if item.error_message:
                item.error_message = ""
                changed_fields.append("error_message")
            if changed_fields:
                item.save(update_fields=changed_fields)

        self.refresh_summary(feed=feed)
        return feed, item

    def refresh_summary(self, *, feed) -> None:
        feed.summary_data = {
            "items_count": feed.items.count(),
            "rows_count": sum(len(item.payload_data.get("rows") or []) for item in feed.items.all()),
        }
        feed.save(update_fields=["summary_data", "updated_at"])

    def _merge_action(self, *, existing_item, new_action: str, existing_feed, remote_product, sales_channel_view):
        if existing_item is None:
            existing_item = SalesChannelFeedItem.objects.filter(
                feed=existing_feed,
                remote_product=remote_product,
                sales_channel_view=sales_channel_view,
            ).first()
        current_action = getattr(existing_item, "action", "")
        if new_action == SalesChannelFeedItem.ACTION_DELETE:
            return SalesChannelFeedItem.ACTION_DELETE
        if current_action == SalesChannelFeedItem.ACTION_CREATE and new_action == SalesChannelFeedItem.ACTION_UPDATE:
            return SalesChannelFeedItem.ACTION_CREATE
        return new_action or current_action or SalesChannelFeedItem.ACTION_UPDATE
