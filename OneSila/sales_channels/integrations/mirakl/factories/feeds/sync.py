from __future__ import annotations

from sales_channels.factories.feeds import SalesChannelFeedGatheringFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed
from sales_channels.models import SalesChannelFeedItem

from .offers import MiraklOfferItemPayloadFactory
from .product_payloads import (
    MiraklProductCreatePayloadFactory,
    MiraklProductDeletePayloadFactory,
    MiraklProductUpdatePayloadFactory,
    _BaseMiraklProductPayloadFactory,
)


class _BaseMiraklProductFeedSyncFactory:
    action = SalesChannelFeedItem.ACTION_UPDATE
    payload_factory_class = _BaseMiraklProductPayloadFactory

    def __init__(self, *, remote_product, sales_channel_view) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.sales_channel_view = sales_channel_view
        self.feed = None
        self.feed_item = None
        self.rows = []

    def run(self):
        self.rows = self._build_rows()
        if not self.rows:
            return None
        self.feed, self.feed_item = self._upsert_feed_item()
        return self.feed_item

    def _build_rows(self):
        return self.payload_factory_class(
            remote_product=self.remote_product,
            sales_channel_view=self.sales_channel_view,
        ).build()

    def _build_feed_item_payload(self):
        return {
            "rows": self.rows,
            "offer": MiraklOfferItemPayloadFactory(
                remote_product=self.remote_product,
                rows=self.rows,
                default_action=self.action,
            ).build(),
        }

    def _get_identifier(self) -> str:
        local_product = getattr(self.remote_product, "local_instance", None)
        return getattr(local_product, "sku", "") or getattr(self.remote_product, "remote_sku", "") or ""

    def _get_feed_factory(self) -> SalesChannelFeedGatheringFactory:
        return SalesChannelFeedGatheringFactory(
            sales_channel=self.sales_channel,
            feed_model_class=MiraklSalesChannelFeed,
            feed_type=MiraklSalesChannelFeed.TYPE_PRODUCT,
            feed_defaults={
                "stage": MiraklSalesChannelFeed.STAGE_PRODUCT,
                "raw_data": {},
            },
        )

    def _upsert_feed_item(self):
        return self._get_feed_factory().upsert_item(
            remote_product=self.remote_product,
            action=self.action,
            payload_data=self._build_feed_item_payload(),
            identifier=self._get_identifier(),
            sales_channel_view=self.sales_channel_view,
        )


class MiraklProductCreateFactory(_BaseMiraklProductFeedSyncFactory):
    action = SalesChannelFeedItem.ACTION_CREATE
    payload_factory_class = MiraklProductCreatePayloadFactory


class MiraklProductUpdateFactory(_BaseMiraklProductFeedSyncFactory):
    action = SalesChannelFeedItem.ACTION_UPDATE
    payload_factory_class = MiraklProductUpdatePayloadFactory


class MiraklProductDeleteFactory(_BaseMiraklProductFeedSyncFactory):
    action = SalesChannelFeedItem.ACTION_DELETE
    payload_factory_class = MiraklProductDeletePayloadFactory
