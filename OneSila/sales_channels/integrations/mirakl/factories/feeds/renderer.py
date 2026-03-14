from __future__ import annotations

import csv
import io

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeedItem


class MiraklProductFeedFileFactory:
    """Render stored Mirakl feed-item payload rows into the product-type template CSV."""

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel
        self.product_type = getattr(feed, "product_type", None)

    def run(self) -> str:
        headers = self._get_template_headers()
        rows = self._get_rows()

        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=headers,
            delimiter=self.sales_channel.csv_delimiter,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})

        filename = self._build_filename()
        if self.feed.file:
            self.feed.file.delete(save=False)
        self.feed.file.save(filename, ContentFile(buffer.getvalue()), save=False)
        self.feed.last_synced_at = timezone.now()
        self.feed.save(update_fields=["file", "last_synced_at"])
        return filename

    def _get_template_headers(self) -> list[str]:
        if self.product_type is None:
            raise ValidationError("Mirakl feed is missing product type.")
        if not self.product_type.template:
            raise ValidationError(f"Mirakl product type '{self.product_type}' is missing a CSV template.")

        with self.product_type.template.open("r") as file_handle:
            reader = csv.reader(file_handle, delimiter=self.sales_channel.csv_delimiter)
            try:
                headers = next(reader)
            except StopIteration as exc:
                raise ValidationError(f"Mirakl template for '{self.product_type}' is empty.") from exc

        normalized_headers = [str(header or "").strip() for header in headers]
        if not any(normalized_headers):
            raise ValidationError(f"Mirakl template for '{self.product_type}' has no headers.")
        return normalized_headers

    def _get_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        queryset = MiraklSalesChannelFeedItem.objects.filter(feed=self.feed).select_related(
            "remote_product",
            "remote_product__local_instance",
            "sales_channel_view",
        ).order_by("id")
        for item in queryset.iterator():
            for row in item.payload_data or []:
                rows.append({str(key): self._stringify(value) for key, value in (row or {}).items()})
        return rows

    def _build_filename(self) -> str:
        product_type_part = slugify(getattr(self.product_type, "remote_id", "") or getattr(self.product_type, "name", "") or "product-type")
        view_part = slugify(getattr(getattr(self.feed, "sales_channel_view", None), "remote_id", "") or getattr(getattr(self.feed, "sales_channel_view", None), "name", "") or "default-view")
        seller_name = getattr(self.sales_channel, "name", None) or getattr(self.sales_channel, "hostname", None) or "mirakl"
        seller_slug = slugify(seller_name) or f"channel-{self.feed.sales_channel_id}"
        return f"mirakl-product-feed-{self.feed.sales_channel_id}-{seller_slug}-{product_type_part}-{view_part}-{self.feed.id or 'new'}.csv"

    def _stringify(self, value) -> str:
        if value in (None, ""):
            return ""
        return str(value)
