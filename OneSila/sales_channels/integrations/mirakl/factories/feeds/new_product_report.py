from __future__ import annotations

import csv
import io
from collections import OrderedDict
from typing import Iterable

from integrations.models import IntegrationLog
from sales_channels.exceptions import MiraklNewProductReportLookupError
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklEanCode,
    MiraklProduct,
    MiraklProperty,
    MiraklSalesChannelFeedItem,
)


class MiraklNewProductReportSyncFactory(GetMiraklAPIMixin):
    """Resolve Mirakl added-product CSV rows back into local MiraklProduct identifiers."""

    DEFAULT_PRODUCT_REFERENCE_TYPE = "EAN"
    LOG_IDENTIFIER = "MiraklNewProductReportSyncFactory:run"
    LOG_FIX_IDENTIFIER = "MiraklNewProductReportSyncFactory:resolved"

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = self._resolve_sales_channel_instance(feed=feed)
        self.reference_headers = self._get_reference_headers()

    def run(self) -> int:
        rows = self._load_rows()
        if not rows:
            return 0

        remote_product_lookup = self._build_remote_product_lookup()
        rows_by_reference = self._group_rows_by_reference(rows=rows)
        if not rows_by_reference:
            return 0

        products_by_reference = self._fetch_products_by_reference(
            references=list(rows_by_reference.keys()),
        )

        unresolved_messages: list[str] = []
        synced_remote_product_ids: set[int] = set()
        for reference, reference_rows in rows_by_reference.items():
            remote_product = self._resolve_remote_product(
                reference=reference,
                remote_product_lookup=remote_product_lookup,
            )
            if remote_product is None:
                unresolved_messages.append(
                    f"EAN {reference} is present in the added products report but was not matched to any local Mirakl product."
                )
                continue

            product_payload = products_by_reference.get(reference)
            if product_payload is None:
                unresolved_messages.append(
                    f"EAN {reference} is marked as added by Mirakl but P31 did not return a product."
                )
                continue
            if not str(product_payload.get("product_sku") or "").strip():
                unresolved_messages.append(
                    f"EAN {reference} is marked as added by Mirakl but P31 did not return a remote product_sku."
                )
                continue
            if not str(product_payload.get("product_id") or "").strip():
                unresolved_messages.append(
                    f"EAN {reference} is marked as added by Mirakl but P31 did not return a remote product_id."
                )
                continue

            self._sync_remote_product(
                remote_product=remote_product,
                product_payload=product_payload,
                report_rows=reference_rows,
                reference=reference,
            )
            synced_remote_product_ids.add(remote_product.id)

        if unresolved_messages:
            self._log_lookup_failure(
                unresolved_messages=unresolved_messages,
                references=list(rows_by_reference.keys()),
            )
            raise MiraklNewProductReportLookupError("\n".join(unresolved_messages))

        self._log_lookup_success(
            references=list(rows_by_reference.keys()),
            synced_count=len(synced_remote_product_ids),
        )
        return len(synced_remote_product_ids)

    def _resolve_sales_channel_instance(self, *, feed):
        sales_channel = feed.sales_channel
        get_real_instance = getattr(sales_channel, "get_real_instance", None)
        if callable(get_real_instance):
            return get_real_instance()
        return sales_channel

    def _load_rows(self) -> list[dict[str, str]]:
        if not self.feed.new_product_report_file:
            return []

        try:
            with self.feed.new_product_report_file.open("rb") as file_handle:
                content = file_handle.read()
        except OSError:
            return []
        if not content:
            return []

        text = self._decode_csv_bytes(content=content)
        if not text.strip():
            return []

        dialect = self._detect_csv_dialect(text=text)
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            if not isinstance(raw_row, dict):
                continue
            row = {
                self._normalize_header(value=header): self._stringify(value=value)
                for header, value in raw_row.items()
                if header is not None
            }
            if any(value for value in row.values()):
                rows.append(row)
        return rows

    def _decode_csv_bytes(self, *, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    def _detect_csv_dialect(self, *, text: str):
        sample = text[:4096]
        try:
            return csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            return csv.excel

    def _group_rows_by_reference(self, *, rows: list[dict[str, str]]) -> OrderedDict[str, list[dict[str, str]]]:
        grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
        missing_references: list[str] = []
        for index, row in enumerate(rows, start=2):
            reference = self._extract_reference(row=row)
            if not reference:
                fallback_identifier = row.get("product_id") or row.get("parent_product_id") or f"line {index}"
                missing_references.append(str(fallback_identifier))
                continue
            grouped.setdefault(reference, []).append(row)

        if missing_references:
            joined = ", ".join(missing_references[:10])
            self._log_lookup_failure(
                unresolved_messages=[
                    "Mirakl added-product rows are missing an EAN reference: {}".format(joined)
                ],
                references=list(grouped.keys()),
            )
            raise MiraklNewProductReportLookupError(
                "Mirakl added-product rows are missing an EAN reference: {}".format(joined)
            )

        return grouped

    def _extract_reference(self, *, row: dict[str, str]) -> str:
        for header in self.reference_headers:
            value = self._normalize_lookup_value(value=row.get(header))
            if value:
                return value
        return ""

    def _get_reference_headers(self) -> list[str]:
        headers: list[str] = []
        if self.feed.product_type_id:
            headers.extend(
                self.feed.product_type.items.filter(
                    remote_property__representation_type=MiraklProperty.REPRESENTATION_PRODUCT_EAN,
                )
                .select_related("remote_property")
                .values_list("remote_property__code", flat=True)
            )

        headers.extend(
            MiraklProperty.objects.filter(
                sales_channel=self.sales_channel,
                representation_type=MiraklProperty.REPRESENTATION_PRODUCT_EAN,
            ).values_list("code", flat=True)
        )

        normalized = [
            self._normalize_header(value=header)
            for header in headers
            if self._normalize_header(value=header)
        ]
        deduped = list(dict.fromkeys(normalized))
        if deduped:
            return deduped

        raise MiraklNewProductReportLookupError(
            "No Mirakl product EAN property is configured for this sales channel."
        )

    def _build_remote_product_lookup(self) -> dict[str, MiraklProduct]:
        lookup: dict[str, MiraklProduct] = {}
        queryset = MiraklSalesChannelFeedItem.objects.filter(feed=self.feed).select_related("remote_product")
        for item in queryset.iterator():
            remote_product = self._resolve_mirakl_product(remote_product=item.remote_product)
            if remote_product is None:
                continue
            for row in self._iter_item_rows(item=item):
                reference = self._extract_reference(row=row)
                if reference:
                    lookup[reference] = remote_product

        ean_matches = (
            MiraklEanCode.objects.filter(remote_product__sales_channel=self.sales_channel)
            .select_related("remote_product")
            .order_by("id")
        )
        for ean_match in ean_matches.iterator():
            remote_product = self._resolve_mirakl_product(remote_product=ean_match.remote_product)
            reference = self._normalize_lookup_value(value=ean_match.ean_code)
            if remote_product is None or not reference or reference in lookup:
                continue
            lookup[reference] = remote_product

        return lookup

    def _iter_item_rows(self, *, item: MiraklSalesChannelFeedItem) -> Iterable[dict[str, str]]:
        payload_data = item.payload_data or []
        rows = payload_data if isinstance(payload_data, list) else [payload_data]
        for row in rows:
            if not isinstance(row, dict):
                continue
            yield {
                self._normalize_header(value=key): self._stringify(value=value)
                for key, value in row.items()
            }

    def _resolve_remote_product(
        self,
        *,
        reference: str,
        remote_product_lookup: dict[str, MiraklProduct],
    ) -> MiraklProduct | None:
        matched = remote_product_lookup.get(reference)
        if matched is not None:
            return matched

        ean_match = (
            MiraklEanCode.objects.filter(
                remote_product__sales_channel=self.sales_channel,
                ean_code=reference,
            )
            .select_related("remote_product")
            .order_by("id")
            .first()
        )
        if ean_match is None:
            return None
        return self._resolve_mirakl_product(remote_product=ean_match.remote_product)

    def _fetch_products_by_reference(self, *, references: list[str]) -> dict[str, dict]:
        products_by_reference: dict[str, dict] = {}
        for chunk in self._chunked(values=references, size=100):
            payload = self.mirakl_get(
                path="/api/products",
                params={
                    "product_references": ",".join(
                        f"{self.DEFAULT_PRODUCT_REFERENCE_TYPE}|{reference}"
                        for reference in chunk
                    )
                },
            )
            for product in payload.get("products") or []:
                if not isinstance(product, dict):
                    continue
                product_id_type = str(product.get("product_id_type") or "").strip().upper()
                if product_id_type and product_id_type != self.DEFAULT_PRODUCT_REFERENCE_TYPE:
                    continue
                reference = self._normalize_lookup_value(value=product.get("product_id"))
                if reference:
                    products_by_reference[reference] = product
        return products_by_reference

    def _chunked(self, *, values: list[str], size: int) -> Iterable[list[str]]:
        for index in range(0, len(values), size):
            yield values[index:index + size]

    def _sync_remote_product(
        self,
        *,
        remote_product: MiraklProduct,
        product_payload: dict,
        report_rows: list[dict[str, str]],
        reference: str,
    ) -> None:
        updates: list[str] = []

        remote_sku = str(product_payload.get("product_sku") or "").strip()
        remote_id = str(product_payload.get("product_id") or "").strip()
        product_id_type = str(product_payload.get("product_id_type") or "").strip().upper()
        title = str(product_payload.get("product_title") or "").strip()

        if remote_product.remote_sku != remote_sku:
            remote_product.remote_sku = remote_sku or None
            updates.append("remote_sku")
        if remote_product.remote_id != remote_id:
            remote_product.remote_id = remote_id or None
            updates.append("remote_id")
        if remote_product.product_id_type != product_id_type:
            remote_product.product_id_type = product_id_type
            updates.append("product_id_type")
        if remote_product.product_reference != remote_id:
            remote_product.product_reference = remote_id
            updates.append("product_reference")
        if title and remote_product.title != title:
            remote_product.title = title
            updates.append("title")
        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100
            updates.append("syncing_current_percentage")

        raw_data = dict(remote_product.raw_data or {})
        raw_data["new_product_report"] = report_rows[-1]
        raw_data["new_product_report_lookup"] = product_payload
        if remote_product.raw_data != raw_data:
            remote_product.raw_data = raw_data
            updates.append("raw_data")

        if updates:
            remote_product.save(update_fields=updates, skip_status_check=False)

        MiraklEanCode.objects.get_or_create(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            ean_code=reference,
        )

    def _resolve_mirakl_product(self, *, remote_product) -> MiraklProduct | None:
        resolved = remote_product
        get_real_instance = getattr(resolved, "get_real_instance", None)
        if callable(get_real_instance):
            resolved = get_real_instance()
        return resolved if isinstance(resolved, MiraklProduct) else None

    def _normalize_header(self, *, value) -> str:
        normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        return normalized.lstrip("\ufeff")

    def _normalize_lookup_value(self, *, value) -> str:
        return self._stringify(value=value).strip()

    def _stringify(self, *, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _log_lookup_failure(self, *, unresolved_messages: list[str], references: list[str]) -> None:
        message = "\n".join(unresolved_messages)
        self.sales_channel.add_user_error(
            action=IntegrationLog.ACTION_UPDATE,
            response=message,
            payload={
                "feed_id": self.feed.id,
                "feed_remote_id": self.feed.remote_id,
                "references": references,
            },
            error_traceback="",
            identifier=self.LOG_IDENTIFIER,
            fixing_identifier=self.LOG_FIX_IDENTIFIER,
        )

    def _log_lookup_success(self, *, references: list[str], synced_count: int) -> None:
        self.sales_channel.add_log(
            action=IntegrationLog.ACTION_UPDATE,
            response="Mirakl added-products report synced.",
            payload={
                "feed_id": self.feed.id,
                "feed_remote_id": self.feed.remote_id,
                "references": references,
                "synced_count": synced_count,
            },
            identifier=self.LOG_FIX_IDENTIFIER,
        )
