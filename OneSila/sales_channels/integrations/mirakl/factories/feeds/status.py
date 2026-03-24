from __future__ import annotations

import logging
import mimetypes
import re
from datetime import timezone as datetime_timezone

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeed, MiraklSalesChannelFeedItem
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem

logger = logging.getLogger(__name__)


class MiraklImportStatusSyncFactory(GetMiraklAPIMixin):
    """Refresh Mirakl product-import statuses through P51 and pull report artifacts when available."""

    RESULTS_KEY = "product_import_trackings"
    CONTENT_DISPOSITION_FILENAME_RE = re.compile(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?')
    TRANSITIONAL_STATUSES = {
        "TRANSFORMATION_WAITING",
        "TRANSFORMATION_RUNNING",
        "TRANSFORMATION_FAILED",
        "WAITING",
        "RUNNING",
        "SENT",
    }
    FINAL_REMOTE_STATUSES = {"COMPLETE", "FAILED", "CANCELLED"}

    def __init__(self, *, sales_channel) -> None:
        self.sales_channel = sales_channel

    def run(self) -> list[MiraklSalesChannelFeed]:
        boundary = timezone.now()
        trackings = self._fetch_trackings()
        local_feeds = self._get_local_feeds()
        feed_by_remote_id = {
            str(feed.remote_id): feed
            for feed in local_feeds
            if str(feed.remote_id or "").strip()
        }

        refreshed: list[MiraklSalesChannelFeed] = []
        for tracking in trackings:
            remote_id = str(tracking.get("import_id") or "").strip()
            if not remote_id:
                continue

            feed = feed_by_remote_id.get(remote_id)
            if feed is None:
                continue

            self._update_feed_from_payload(feed=feed, payload=tracking)
            self._sync_reports(feed=feed)
            self._handle_completion(feed=feed)
            refreshed.append(feed)

        self.sales_channel.last_product_imports_request_date = boundary
        self.sales_channel.save(update_fields=["last_product_imports_request_date"])
        return refreshed

    def _fetch_trackings(self) -> list[dict]:
        params: dict[str, str] = {}
        if self.sales_channel.last_product_imports_request_date is not None:
            params["last_request_date"] = self._format_datetime(
                value=self.sales_channel.last_product_imports_request_date,
            )
        return self.mirakl_paginated_get(
            path="/api/products/imports",
            results_key=self.RESULTS_KEY,
            params=params or None,
        )

    def _get_local_feeds(self):
        return list(
            MiraklSalesChannelFeed.objects.filter(
                sales_channel=self.sales_channel,
                remote_id__gt="",
                status=SalesChannelFeed.STATUS_SUBMITTED,
            )
            .select_related("sales_channel", "product_type", "sales_channel_view")
            .order_by("-id")
        )

    def _update_feed_from_payload(self, *, feed: MiraklSalesChannelFeed, payload: dict) -> None:
        raw_status = str(payload.get("import_status") or payload.get("status") or "").upper()
        raw_data = dict(feed.raw_data or {})
        raw_data["product_status_response"] = payload

        integration_details = payload.get("integration_details") or {}
        conversion_options = payload.get("conversion_options") or {}

        feed.import_status = raw_status
        feed.reason_status = str(payload.get("reason_status") or payload.get("reason") or "")
        feed.remote_shop_id = payload.get("shop_id") or feed.remote_shop_id
        feed.remote_date_created = parse_datetime(payload.get("date_created") or "") if payload.get("date_created") else feed.remote_date_created
        feed.conversion_type = str(payload.get("conversion_type") or "")
        feed.conversion_options_ai_enrichment_enabled = self._is_enabled(
            conversion_options.get("ai_enrichment"),
        )
        feed.conversion_options_ai_rewrite_enabled = self._is_enabled(
            conversion_options.get("ai_rewrite"),
        )
        feed.integration_details_invalid_products = self._to_int(integration_details.get("invalid_products"))
        feed.integration_details_products_not_accepted_in_time = self._to_int(
            integration_details.get("products_not_accepted_in_time")
        )
        feed.integration_details_products_not_synchronized_in_time = self._to_int(
            integration_details.get("products_not_synchronized_in_time")
        )
        feed.integration_details_products_reimported = self._to_int(
            integration_details.get("products_reimported")
        )
        feed.integration_details_products_successfully_synchronized = self._to_int(
            integration_details.get("products_successfully_synchronized")
        )
        feed.integration_details_products_with_synchronization_issues = self._to_int(
            integration_details.get("products_with_synchronization_issues")
        )
        feed.integration_details_products_with_wrong_identifiers = self._to_int(
            integration_details.get("products_with_wrong_identifiers")
        )
        feed.integration_details_rejected_products = self._to_int(
            integration_details.get("rejected_products")
        )
        feed.has_error_report = bool(payload.get("has_error_report"))
        feed.has_new_product_report = bool(payload.get("has_new_product_report"))
        feed.has_transformation_error_report = bool(payload.get("has_transformation_error_report"))
        feed.has_transformed_file = bool(payload.get("has_transformed_file"))
        feed.transform_lines_read = self._to_int(payload.get("transform_lines_read"))
        feed.transform_lines_in_success = self._to_int(payload.get("transform_lines_in_success"))
        feed.transform_lines_in_error = self._to_int(payload.get("transform_lines_in_error"))
        feed.transform_lines_with_warning = self._to_int(payload.get("transform_lines_with_warning"))
        feed.last_polled_at = timezone.now()
        feed.raw_data = raw_data
        feed.status = self._map_status(feed=feed, raw_status=raw_status)
        feed.save()

    def _map_status(self, *, feed: MiraklSalesChannelFeed, raw_status: str) -> str:
        if raw_status in self.TRANSITIONAL_STATUSES:
            return SalesChannelFeed.STATUS_SUBMITTED
        if raw_status == "CANCELLED":
            return SalesChannelFeed.STATUS_CANCELLED
        if raw_status == "FAILED":
            return SalesChannelFeed.STATUS_FAILED
        if raw_status == "COMPLETE":
            if feed.transform_lines_in_error and feed.transform_lines_in_success:
                return SalesChannelFeed.STATUS_PARTIAL
            if feed.transform_lines_in_error:
                return SalesChannelFeed.STATUS_FAILED
            return SalesChannelFeed.STATUS_SUCCESS
        return SalesChannelFeed.STATUS_SUBMITTED

    def _sync_reports(self, *, feed: MiraklSalesChannelFeed) -> None:
        if feed.has_error_report and not feed.error_report_file:
            self._download_report(
                feed=feed,
                path=f"/api/products/imports/{feed.remote_id}/error_report",
                field_name="error_report_file",
                filename_base=f"mirakl-product-errors-{feed.remote_id}",
            )
        if feed.has_new_product_report and not feed.new_product_report_file:
            self._download_report(
                feed=feed,
                path=f"/api/products/imports/{feed.remote_id}/new_product_report",
                field_name="new_product_report_file",
                filename_base=f"mirakl-product-success-{feed.remote_id}",
            )
        if feed.has_transformed_file and not feed.transformed_file:
            self._download_report(
                feed=feed,
                path=f"/api/products/imports/{feed.remote_id}/transformed_file",
                field_name="transformed_file",
                filename_base=f"mirakl-product-transformed-{feed.remote_id}",
            )
        if feed.has_transformation_error_report and not feed.transformation_error_report_file:
            self._download_report(
                feed=feed,
                path=f"/api/products/imports/{feed.remote_id}/transformation_error_report",
                field_name="transformation_error_report_file",
                filename_base=f"mirakl-product-transform-errors-{feed.remote_id}",
            )
        if feed.has_transformation_error_report and feed.transformation_error_report_file:
            self._sync_transformation_report_issues(feed=feed)

    def _sync_transformation_report_issues(self, *, feed: MiraklSalesChannelFeed) -> None:
        from sales_channels.integrations.mirakl.factories.feeds.issues_report import (
            MiraklTransformationErrorReportIssueSyncFactory,
        )

        try:
            MiraklTransformationErrorReportIssueSyncFactory(feed=feed).run()
        except Exception:
            logger.exception(
                "Failed to sync Mirakl transformation report issues for feed_id=%s remote_id=%s",
                feed.id,
                feed.remote_id,
            )

    def _download_report(
        self,
        *,
        feed: MiraklSalesChannelFeed,
        path: str,
        field_name: str,
        filename_base: str,
    ) -> None:
        response = self._request(method="GET", path=path, expected_statuses={200})
        content = response.content or b""
        if not content:
            return

        filename = self._resolve_download_filename(
            response=response,
            filename_base=filename_base,
        )
        file_field = getattr(feed, field_name)
        file_field.save(filename, ContentFile(content), save=False)
        feed.save(update_fields=[field_name])

    def _resolve_download_filename(self, *, response, filename_base: str) -> str:
        content_disposition = str(response.headers.get("Content-Disposition") or "")
        match = self.CONTENT_DISPOSITION_FILENAME_RE.search(content_disposition)
        if match:
            filename = str(match.group(1) or "").strip()
            if filename:
                return filename

        content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip()
        extension = mimetypes.guess_extension(content_type or "") or ".csv"
        if extension == ".ksh":
            extension = ".txt"
        if filename_base.endswith(extension):
            return filename_base
        return f"{filename_base}{extension}"

    def _handle_completion(self, *, feed: MiraklSalesChannelFeed) -> None:
        if feed.import_status not in self.FINAL_REMOTE_STATUSES:
            return

        remote_id = feed.product_remote_id or feed.remote_id
        if feed.status in {SalesChannelFeed.STATUS_SUCCESS, SalesChannelFeed.STATUS_PARTIAL}:
            self._mark_items_success(feed=feed, remote_id=remote_id)
            feed.error_message = ""
            feed.save(update_fields=["error_message"])
            return

        message = feed.reason_status or "Mirakl product import failed."
        feed.error_message = message
        feed.save(update_fields=["error_message"])
        self._mark_items_failed(feed=feed, remote_id=remote_id, message=message)

    def _mark_items_success(self, *, feed: MiraklSalesChannelFeed, remote_id: str) -> None:
        for item in MiraklSalesChannelFeedItem.objects.filter(feed=feed).select_related("remote_product"):
            item.status = SalesChannelFeedItem.STATUS_SUCCESS
            item.error_message = ""
            item.save(update_fields=["status", "error_message"])
            item.remote_product.add_log(
                action="mirakl_product_feed",
                response="Mirakl product import completed.",
                payload=item.payload_data,
                identifier=f"mirakl-product-feed-{remote_id}",
                remote_product=item.remote_product,
            )

    def _mark_items_failed(self, *, feed: MiraklSalesChannelFeed, remote_id: str, message: str) -> None:
        for item in MiraklSalesChannelFeedItem.objects.filter(feed=feed).select_related("remote_product"):
            item.status = SalesChannelFeedItem.STATUS_FAILED
            item.error_message = message
            item.save(update_fields=["status", "error_message"])
            item.remote_product.add_error(
                action="mirakl_product_feed",
                response=message,
                payload=item.payload_data,
                error_traceback="",
                identifier=f"mirakl-product-feed-{remote_id}",
                remote_product=item.remote_product,
            )

    def _is_enabled(self, payload) -> bool:
        if not isinstance(payload, dict):
            return False
        return str(payload.get("status") or "").upper() == "ENABLED"

    def _to_int(self, value) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    def _format_datetime(self, *, value) -> str:
        normalized = value.astimezone(datetime_timezone.utc).replace(microsecond=0)
        return normalized.isoformat().replace("+00:00", "Z")
