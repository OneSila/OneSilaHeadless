from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeedItem
from sales_channels.integrations.mirakl.utils.offer_fields import (
    build_offer_field_key,
    is_explicit_offer_field_header,
    is_offer_field_header,
    normalize_offer_external_key,
)

PLAIN_PRODUCT_PREFERRED_OFFER_HEADERS = {"description"}


class MiraklProductFeedFileFactory:
    """Render stored Mirakl feed-item payload rows into the product-type template CSV."""

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = self._resolve_sales_channel_instance(feed=feed)
        self.product_type = getattr(feed, "product_type", None)
        self._template_delimiter: str | None = None

    def _resolve_sales_channel_instance(self, *, feed):
        sales_channel = feed.sales_channel
        get_real_instance = getattr(sales_channel, "get_real_instance", None)
        if callable(get_real_instance):
            return get_real_instance()
        return sales_channel

    def run(self) -> str:
        headers = self._get_template_headers()
        rows = self._get_rows()
        delimiter = self._template_delimiter or self.sales_channel.csv_delimiter

        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=delimiter,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writerow(headers)
        for row in rows:
            writer.writerow(self._build_output_values(row=row, headers=headers))

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
            try:
                first_line = file_handle.readline()
            except StopIteration as exc:
                raise ValidationError(f"Mirakl template for '{self.product_type}' is empty.") from exc

        if first_line == "":
            raise ValidationError(f"Mirakl template for '{self.product_type}' is empty.")

        delimiter = self._resolve_template_delimiter(first_line=first_line)
        self._template_delimiter = delimiter
        headers = next(csv.reader([first_line], delimiter=delimiter))

        normalized_headers = [str(header or "").strip() for header in headers]
        if not any(normalized_headers):
            raise ValidationError(f"Mirakl template for '{self.product_type}' has no headers.")
        return normalized_headers

    def _resolve_template_delimiter(self, *, first_line: str) -> str:
        configured_delimiter = getattr(self.sales_channel, "csv_delimiter", ",") or ","
        configured_headers = next(csv.reader([first_line], delimiter=configured_delimiter))
        if len(configured_headers) > 1:
            return configured_delimiter

        try:
            dialect = csv.Sniffer().sniff(first_line, delimiters=",;|\t")
            detected_delimiter = str(getattr(dialect, "delimiter", "") or "")
            if detected_delimiter:
                return detected_delimiter
        except csv.Error:
            pass

        for fallback_delimiter in [",", ";", "|", "\t"]:
            fallback_headers = next(csv.reader([first_line], delimiter=fallback_delimiter))
            if len(fallback_headers) > 1:
                return fallback_delimiter

        return configured_delimiter

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

    def _build_output_values(self, *, row: dict[str, str], headers: list[str]) -> list[str]:
        header_counts = Counter(headers)
        explicit_offer_headers = {
            normalize_offer_external_key(external_key=header)
            for header in headers
            if is_explicit_offer_field_header(header=header)
        }
        seen_headers: dict[str, int] = defaultdict(int)
        output_values: list[str] = []
        for header in headers:
            seen_headers[header] += 1
            output_values.append(
                self._resolve_output_value(
                    row=row,
                    header=header,
                    occurrence_index=seen_headers[header],
                    total_occurrences=header_counts[header],
                    explicit_offer_headers=explicit_offer_headers,
                )
            )
        return output_values

    def _resolve_output_value(
        self,
        *,
        row: dict[str, str],
        header: str,
        occurrence_index: int,
        total_occurrences: int,
        explicit_offer_headers: set[str],
    ) -> str:
        if is_explicit_offer_field_header(header=header):
            offer_key = build_offer_field_key(external_key=header)
            return row.get(offer_key, row.get(header, ""))

        if not is_offer_field_header(header=header):
            return row.get(header, "")

        normalized_header = normalize_offer_external_key(external_key=header)
        offer_key = build_offer_field_key(external_key=header)
        has_plain_value = header in row
        has_offer_value = offer_key in row
        has_explicit_offer_counterpart = normalized_header in explicit_offer_headers

        if normalized_header in PLAIN_PRODUCT_PREFERRED_OFFER_HEADERS:
            if total_occurrences > 1 and has_offer_value and occurrence_index == total_occurrences:
                return row.get(offer_key, "")
            if has_plain_value:
                return row.get(header, "")
            if has_offer_value:
                return row.get(offer_key, "")
            return row.get(header, "")

        if has_explicit_offer_counterpart and has_plain_value:
            return row.get(header, "")

        if has_offer_value:
            return row.get(offer_key, "")

        return row.get(header, "")

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
