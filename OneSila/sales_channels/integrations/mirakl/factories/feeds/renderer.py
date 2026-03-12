from __future__ import annotations

import csv
import io
import json

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify


class MiraklProductFeedFileFactory:
    """Render normalized Mirakl product payloads into a CSV artifact."""

    FIELDNAMES = [
        "update-delete",
        "shop-sku",
        "product-id",
        "product-id-type",
        "title",
        "description",
        "brand",
        "category-code",
        "variant-group-code",
        "main-image-url",
        "additional-image-urls",
        "attributes-json",
        "prices-json",
    ]

    def __init__(self, *, feed) -> None:
        self.feed = feed

    def run(self) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.FIELDNAMES, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for item in self.feed.items.all():
            for row in item.payload_data.get("rows") or []:
                images = list(row.get("images") or [])
                main_image = next((image.get("url") for image in images if image.get("is_main")), "")
                additional_images = [image.get("url") for image in images if image.get("url") and image.get("url") != main_image]
                writer.writerow(
                    {
                        "update-delete": row.get("action", ""),
                        "shop-sku": row.get("sku", ""),
                        "product-id": row.get("ean") or row.get("sku") or "",
                        "product-id-type": "EAN" if row.get("ean") else "SHOP_SKU",
                        "title": row.get("name", ""),
                        "description": row.get("description") or row.get("short_description") or "",
                        "brand": row.get("brand", ""),
                        "category-code": (row.get("category") or {}).get("remote_id", ""),
                        "variant-group-code": row.get("variant_group_code", ""),
                        "main-image-url": main_image,
                        "additional-image-urls": json.dumps(additional_images, ensure_ascii=False),
                        "attributes-json": json.dumps(row.get("attributes") or [], ensure_ascii=False, default=str),
                        "prices-json": json.dumps(row.get("prices") or [], ensure_ascii=False, default=str),
                    }
                )

        filename = self._build_filename()
        content = buffer.getvalue()
        if self.feed.file:
            self.feed.file.delete(save=False)
        self.feed.file.save(filename, ContentFile(content), save=False)
        self.feed.last_synced_at = timezone.now()
        self.feed.save(update_fields=["file", "last_synced_at"])
        return filename

    def _build_filename(self) -> str:
        seller_name = getattr(self.feed.sales_channel, "name", None) or getattr(self.feed.sales_channel, "hostname", None) or "mirakl"
        seller_slug = slugify(seller_name) or f"channel-{self.feed.sales_channel_id}"
        return f"mirakl-{self.feed.stage}-feed-{self.feed.sales_channel_id}-{seller_slug}-{self.feed.id or 'new'}.csv"
