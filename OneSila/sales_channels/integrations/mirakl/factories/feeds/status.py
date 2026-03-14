from __future__ import annotations

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeedItem
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


class MiraklImportStatusSyncFactory(GetMiraklAPIMixin):
    """Refresh a Mirakl product import status and pull report artifacts when available."""

    FINAL_STATUSES = {"COMPLETE", "FAILED", "CANCELLED"}
    PENDING_STATUSES = {"WAITING", "RUNNING", "SENT"}

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel

    def run(self):
        if not self.feed.remote_id:
            raise ValueError("Mirakl feed is missing remote_id.")

        payload = self.mirakl_get(path=f"/api/products/imports/{self.feed.remote_id}")
        self._update_from_payload(payload=payload)
        self._sync_reports()
        self._handle_completion()
        return self.feed

    def _update_from_payload(self, *, payload: dict) -> None:
        raw_status = str(payload.get("import_status") or payload.get("status") or "").upper()
        raw_data = dict(self.feed.raw_data or {})
        raw_data["product_status_response"] = payload

        self.feed.import_status = raw_status
        self.feed.reason_status = str(payload.get("reason_status") or payload.get("reason") or "")
        self.feed.remote_shop_id = payload.get("shop_id") or self.feed.remote_shop_id
        self.feed.remote_date_created = parse_datetime(payload.get("date_created") or "") if payload.get("date_created") else self.feed.remote_date_created
        self.feed.has_error_report = bool(payload.get("has_error_report"))
        self.feed.has_new_product_report = bool(payload.get("has_new_product_report"))
        self.feed.has_transformation_error_report = bool(payload.get("has_transformation_error_report"))
        self.feed.has_transformed_file = bool(payload.get("has_transformed_file"))
        self.feed.transform_lines_read = int(payload.get("transform_lines_read") or 0)
        self.feed.transform_lines_in_success = int(payload.get("transform_lines_in_success") or 0)
        self.feed.transform_lines_in_error = int(payload.get("transform_lines_in_error") or 0)
        self.feed.transform_lines_with_warning = int(payload.get("transform_lines_with_warning") or 0)
        self.feed.last_polled_at = timezone.now()
        self.feed.raw_data = raw_data
        self.feed.status = self._map_status(raw_status=raw_status)
        self.feed.save()

    def _map_status(self, *, raw_status: str) -> str:
        if raw_status in self.PENDING_STATUSES:
            return SalesChannelFeed.STATUS_PROCESSING
        if raw_status in {"FAILED", "CANCELLED"}:
            return SalesChannelFeed.STATUS_FAILED
        if raw_status == "COMPLETE":
            if self.feed.transform_lines_in_error and self.feed.transform_lines_in_success:
                return SalesChannelFeed.STATUS_PARTIAL
            if self.feed.transform_lines_in_error:
                return SalesChannelFeed.STATUS_FAILED
            return SalesChannelFeed.STATUS_SUCCESS
        return SalesChannelFeed.STATUS_PROCESSING

    def _sync_reports(self) -> None:
        if self.feed.has_error_report and not self.feed.error_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.feed.remote_id}/error_report",
                field_name="error_report_file",
                filename=f"mirakl-product-errors-{self.feed.remote_id}.csv",
            )
        if self.feed.has_new_product_report and not self.feed.new_product_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.feed.remote_id}/new_product_report",
                field_name="new_product_report_file",
                filename=f"mirakl-product-success-{self.feed.remote_id}.csv",
            )
        if self.feed.has_transformed_file and not self.feed.transformed_file:
            self._download_report(
                path=f"/api/products/imports/{self.feed.remote_id}/transformed_file",
                field_name="transformed_file",
                filename=f"mirakl-product-transformed-{self.feed.remote_id}.csv",
            )
        if self.feed.has_transformation_error_report and not self.feed.transformation_error_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.feed.remote_id}/transformation_error_report",
                field_name="transformation_error_report_file",
                filename=f"mirakl-product-transform-errors-{self.feed.remote_id}.csv",
            )

    def _download_report(self, *, path: str, field_name: str, filename: str) -> None:
        response = self._request(method="GET", path=path, expected_statuses={200})
        content = response.content or b""
        if not content:
            return
        file_field = getattr(self.feed, field_name)
        file_field.save(filename, ContentFile(content), save=False)
        self.feed.save(update_fields=[field_name])

    def _handle_completion(self) -> None:
        if self.feed.import_status not in self.FINAL_STATUSES:
            return

        remote_id = self.feed.product_remote_id or self.feed.remote_id
        if self.feed.status in {SalesChannelFeed.STATUS_SUCCESS, SalesChannelFeed.STATUS_PARTIAL}:
            self._mark_items_success(remote_id=remote_id)
            self.feed.error_message = ""
            self.feed.save(update_fields=["error_message"])
            return

        message = self.feed.reason_status or "Mirakl product import failed."
        self.feed.error_message = message
        self.feed.save(update_fields=["error_message"])
        self._mark_items_failed(remote_id=remote_id, message=message)

    def _mark_items_success(self, *, remote_id: str) -> None:
        for item in MiraklSalesChannelFeedItem.objects.filter(feed=self.feed).select_related("remote_product"):
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

    def _mark_items_failed(self, *, remote_id: str, message: str) -> None:
        for item in MiraklSalesChannelFeedItem.objects.filter(feed=self.feed).select_related("remote_product"):
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
