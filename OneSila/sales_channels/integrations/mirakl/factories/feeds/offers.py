from __future__ import annotations

from typing import Any

from sales_channels.models import SalesChannelFeedItem


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
            price = row.get("price")
            if action != SalesChannelFeedItem.ACTION_DELETE and price in (None, ""):
                prices = row.get("prices") or []
                primary_price = prices[0] if prices else {}
                price = primary_price.get("price")
            if action != SalesChannelFeedItem.ACTION_DELETE and price in (None, ""):
                continue

            product_id = (
                getattr(self.remote_product, "product_reference", "")
                or row.get("product_id")
                or row.get("product_ean")
                or row.get("ean")
                or getattr(self.remote_product, "remote_id", "")
                or row.get("sku")
            )
            if not product_id:
                continue

            offer_payload: dict[str, Any] = {
                "shop_sku": row.get("sku") or getattr(self.remote_product, "remote_sku", ""),
                "product_id": product_id,
                "product_id_type": getattr(self.remote_product, "product_id_type", "") or ("EAN" if row.get("product_ean") or row.get("ean") else "SHOP_SKU"),
                "price": price,
                "description": row.get("product_description") or row.get("description") or row.get("product_short_description") or row.get("short_description") or row.get("name") or "",
                "internal_description": row.get("name") or row.get("sku") or "",
                "update_delete": action,
                "state_code": row.get("condition") or raw_data.get("state_code") or "11",
            }
            discount_price = row.get("discounted_price")
            if discount_price not in (None, ""):
                offer_payload["discount"] = {"price": discount_price}
            if send_quantity:
                quantity = row.get("stock") or raw_data.get("initial_quantity") or raw_data.get("quantity") or 0
                if quantity:
                    offer_payload["quantity"] = str(quantity)
            offers.append(offer_payload)

        return offers


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
