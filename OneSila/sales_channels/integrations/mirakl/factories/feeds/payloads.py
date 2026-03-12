from __future__ import annotations

from typing import Any

from sales_channels.factories.feeds import SalesChannelFeedGatheringFactory
from sales_channels.factories.feeds import SalesChannelFeedProductPayloadFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed
from sales_channels.models import SalesChannelFeedItem


class _BaseMiraklProductPayloadFactory:
    action = "update"

    def __init__(self, *, remote_product) -> None:
        self.remote_product = remote_product

    def build(self) -> list[dict[str, Any]]:
        payloads = SalesChannelFeedProductPayloadFactory(remote_product=self.remote_product).build()
        for payload in payloads:
            payload["action"] = self.action
        return payloads


class MiraklProductCreatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_CREATE


class MiraklProductUpdatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductDeletePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_DELETE


class MiraklOfferItemPayloadFactory:
    """Build OF24-ready offer payloads for one gathered feed item."""

    def __init__(self, *, remote_product, rows: list[dict[str, Any]], default_action: str = "") -> None:
        self.remote_product = remote_product
        self.rows = list(rows or [])
        self.default_action = default_action

    def build(self) -> list[dict[str, Any]]:
        offers: list[dict[str, Any]] = []
        raw_data = dict(getattr(self.remote_product, "raw_data", {}) or {})
        send_quantity = not raw_data.get("offer_created")

        for row in self.rows:
            action = row.get("action") or self.default_action
            prices = row.get("prices") or []
            primary_price = prices[0] if prices else {}
            price = primary_price.get("price")
            if action != SalesChannelFeedItem.ACTION_DELETE and price in (None, ""):
                continue

            product_id = (
                getattr(self.remote_product, "product_reference", "")
                or row.get("ean")
                or getattr(self.remote_product, "remote_id", "")
                or row.get("sku")
            )
            if not product_id:
                continue

            offer_payload: dict[str, Any] = {
                "shop_sku": row.get("sku") or getattr(self.remote_product, "remote_sku", ""),
                "product_id": product_id,
                "product_id_type": getattr(self.remote_product, "product_id_type", "") or ("EAN" if row.get("ean") else "SHOP_SKU"),
                "price": price,
                "description": row.get("description") or row.get("short_description") or row.get("name") or "",
                "internal_description": row.get("name") or row.get("sku") or "",
                "update_delete": action,
                "state_code": raw_data.get("state_code") or "11",
            }
            discount = primary_price.get("discount")
            if discount not in (None, ""):
                offer_payload["discount"] = {"price": discount}
            if send_quantity:
                quantity = raw_data.get("initial_quantity") or raw_data.get("quantity") or 0
                if quantity:
                    offer_payload["quantity"] = str(quantity)
            offers.append(offer_payload)

        return offers


class _BaseMiraklProductFeedSyncFactory:
    action = SalesChannelFeedItem.ACTION_UPDATE
    payload_factory_class = _BaseMiraklProductPayloadFactory

    def __init__(self, *, remote_product) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.feed = None
        self.feed_item = None
        self.rows: list[dict[str, Any]] = []

    def run(self):
        self.rows = self._build_rows()
        if not self.rows:
            return None
        self.feed, self.feed_item = self._upsert_feed_item()
        return self.feed_item

    def _build_rows(self) -> list[dict[str, Any]]:
        return self.payload_factory_class(remote_product=self.remote_product).build()

    def _build_feed_item_payload(self) -> dict[str, Any]:
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
            sales_channel_view=None,
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


class MiraklOfferPayloadFactory:
    """Build OF24 payload rows from successful product feed items."""

    def __init__(self, *, feed) -> None:
        self.feed = feed

    def build(self) -> list[dict[str, Any]]:
        offers: list[dict[str, Any]] = []
        for item in self.feed.items.select_related("remote_product", "remote_product__local_instance").all():
            offer_payloads = item.payload_data.get("offer")
            if offer_payloads is None:
                offer_payloads = MiraklOfferItemPayloadFactory(
                    remote_product=item.remote_product,
                    rows=list(item.payload_data.get("rows") or []),
                    default_action=item.action,
                ).build()
            offers.extend(offer_payloads)

        return offers
