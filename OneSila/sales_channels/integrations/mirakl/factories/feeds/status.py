from __future__ import annotations

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from imports_exports.models import Import
from sales_channels.integrations.mirakl.factories.feeds.payloads import MiraklOfferPayloadFactory
from sales_channels.integrations.mirakl.factories.feeds.submit import MiraklOfferSubmitFactory
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.models import SalesChannelFeed, SalesChannelFeedItem


class MiraklImportStatusSyncFactory(GetMiraklAPIMixin):
    """Refresh a Mirakl import status and pull report artifacts when available."""

    FINAL_STATUSES = {"COMPLETE", "FAILED", "CANCELLED"}
    PENDING_STATUSES = {"WAITING", "RUNNING", "SENT"}

    def __init__(self, *, import_process) -> None:
        self.import_process = import_process
        self.sales_channel = import_process.sales_channel

    def run(self):
        if not self.import_process.remote_import_id:
            raise ValueError("Mirakl import is missing remote_import_id.")

        if self.import_process.type == self.import_process.TYPE_PRODUCT:
            payload = self.mirakl_get(path=f"/api/products/imports/{self.import_process.remote_import_id}")
            self._update_from_payload(payload=payload)
            self._sync_product_reports()
            self._handle_product_completion()
        elif self.import_process.type == self.import_process.TYPE_OFFER:
            payload = self.mirakl_get(path=f"/api/offers/imports/{self.import_process.remote_import_id}")
            self._update_from_payload(payload=payload)
            self._sync_offer_reports()
            self._handle_offer_completion()
        return self.import_process

    def _update_from_payload(self, *, payload: dict) -> None:
        raw_status = str(payload.get("import_status") or payload.get("status") or "").upper()
        self.import_process.import_status = raw_status
        self.import_process.reason_status = str(payload.get("reason_status") or payload.get("reason") or "")
        self.import_process.remote_shop_id = payload.get("shop_id") or self.import_process.remote_shop_id
        self.import_process.remote_date_created = parse_datetime(payload.get("date_created") or "") if payload.get("date_created") else self.import_process.remote_date_created
        self.import_process.has_error_report = bool(payload.get("has_error_report"))
        self.import_process.has_new_product_report = bool(payload.get("has_new_product_report"))
        self.import_process.has_transformation_error_report = bool(payload.get("has_transformation_error_report"))
        self.import_process.has_transformed_file = bool(payload.get("has_transformed_file"))
        self.import_process.transform_lines_read = int(payload.get("transform_lines_read") or 0)
        self.import_process.transform_lines_in_success = int(payload.get("transform_lines_in_success") or 0)
        self.import_process.transform_lines_in_error = int(payload.get("transform_lines_in_error") or 0)
        self.import_process.transform_lines_with_warning = int(payload.get("transform_lines_with_warning") or 0)
        self.import_process.raw_response = payload
        self.import_process.summary_data = payload
        self.import_process.status = self._map_status(raw_status=raw_status)
        self.import_process.save()
        if self.import_process.feed_id:
            self.import_process.feed.last_polled_at = timezone.now()
            self.import_process.feed.save(update_fields=["last_polled_at"])

    def _map_status(self, *, raw_status: str) -> str:
        if raw_status in self.PENDING_STATUSES:
            return Import.STATUS_PENDING
        if raw_status == "COMPLETE":
            return Import.STATUS_SUCCESS if self.import_process.transform_lines_in_error == 0 else Import.STATUS_FAILED
        if raw_status in {"FAILED", "CANCELLED"}:
            return Import.STATUS_FAILED
        return Import.STATUS_PROCESSING

    def _sync_product_reports(self) -> None:
        if self.import_process.has_error_report and not self.import_process.error_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.import_process.remote_import_id}/error_report",
                field_name="error_report_file",
                filename=f"mirakl-product-errors-{self.import_process.remote_import_id}.csv",
            )
        if self.import_process.has_new_product_report and not self.import_process.new_product_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.import_process.remote_import_id}/new_product_report",
                field_name="new_product_report_file",
                filename=f"mirakl-product-success-{self.import_process.remote_import_id}.csv",
            )
        if self.import_process.has_transformed_file and not self.import_process.transformed_file:
            self._download_report(
                path=f"/api/products/imports/{self.import_process.remote_import_id}/transformed_file",
                field_name="transformed_file",
                filename=f"mirakl-product-transformed-{self.import_process.remote_import_id}.csv",
            )
        if self.import_process.has_transformation_error_report and not self.import_process.transformation_error_report_file:
            self._download_report(
                path=f"/api/products/imports/{self.import_process.remote_import_id}/transformation_error_report",
                field_name="transformation_error_report_file",
                filename=f"mirakl-product-transform-errors-{self.import_process.remote_import_id}.csv",
            )

    def _sync_offer_reports(self) -> None:
        if self.import_process.has_error_report and not self.import_process.error_report_file:
            self._download_report(
                path=f"/api/offers/imports/{self.import_process.remote_import_id}/error_report",
                field_name="error_report_file",
                filename=f"mirakl-offer-errors-{self.import_process.remote_import_id}.csv",
            )

    def _download_report(self, *, path: str, field_name: str, filename: str) -> None:
        response = self._request(method="GET", path=path, expected_statuses={200})
        content = response.content or b""
        if not content:
            return
        file_field = getattr(self.import_process, field_name)
        file_field.save(filename, ContentFile(content), save=False)
        self.import_process.save(update_fields=[field_name])

    def _handle_product_completion(self) -> None:
        if self.import_process.import_status not in self.FINAL_STATUSES or not self.import_process.feed_id:
            return

        feed = self.import_process.feed
        if self.import_process.status == Import.STATUS_SUCCESS:
            feed.status = SalesChannelFeed.STATUS_PARTIAL
            feed.error_message = ""
            feed.save(update_fields=["status", "error_message"])
            feed.items.update(status=SalesChannelFeedItem.STATUS_SUCCESS)
            if not feed.mirakl_imports.filter(type=self.import_process.TYPE_OFFER).exists():
                offers = MiraklOfferPayloadFactory(feed=feed).build()
                if offers:
                    MiraklOfferSubmitFactory(feed=feed, offers=offers).run()
                else:
                    feed.error_message = "Products imported but no offer payloads were generated."
                    feed.save(update_fields=["error_message"])
            for item in feed.items.select_related("remote_product").all():
                item.remote_product.add_log(
                    action="mirakl_product_feed",
                    response="Mirakl product import completed.",
                    payload=item.payload_data,
                    identifier=f"mirakl-product-feed-{self.import_process.remote_import_id}",
                    remote_product=item.remote_product,
                )
        else:
            feed.status = SalesChannelFeed.STATUS_FAILED
            feed.error_message = self.import_process.reason_status or "Mirakl product import failed."
            feed.save(update_fields=["status", "error_message"])
            for item in feed.items.select_related("remote_product").all():
                item.status = SalesChannelFeedItem.STATUS_FAILED
                item.error_message = self.import_process.reason_status or "Mirakl product import failed."
                item.save(update_fields=["status", "error_message"])
                item.remote_product.add_error(
                    action="mirakl_product_feed",
                    response=item.error_message,
                    payload=item.payload_data,
                    error_traceback=self.import_process.error_traceback or "",
                    identifier=f"mirakl-product-feed-{self.import_process.remote_import_id}",
                    remote_product=item.remote_product,
                )

    def _handle_offer_completion(self) -> None:
        if self.import_process.import_status not in self.FINAL_STATUSES or not self.import_process.feed_id:
            return
        feed = self.import_process.feed
        if self.import_process.status == Import.STATUS_SUCCESS:
            if feed.status != SalesChannelFeed.STATUS_SUCCESS:
                feed.status = SalesChannelFeed.STATUS_SUCCESS
                feed.error_message = ""
                feed.save(update_fields=["status", "error_message"])
            for item in feed.items.select_related("remote_product").all():
                remote_product = item.remote_product
                raw_data = dict(getattr(remote_product, "raw_data", {}) or {})
                raw_data["offer_created"] = True
                remote_product.raw_data = raw_data
                remote_product.save(update_fields=["raw_data"])
                remote_product.add_log(
                    action="mirakl_offer_publish",
                    response="Mirakl offer publish completed.",
                    payload=item.payload_data,
                    identifier=f"mirakl-offer-feed-{self.import_process.remote_import_id}",
                    remote_product=remote_product,
                )
        else:
            feed.status = SalesChannelFeed.STATUS_PARTIAL
            feed.error_message = self.import_process.reason_status or "Mirakl offer publish failed."
            feed.save(update_fields=["status", "error_message"])
            for item in feed.items.select_related("remote_product").all():
                item.remote_product.add_error(
                    action="mirakl_offer_publish",
                    response=feed.error_message,
                    payload=item.payload_data,
                    error_traceback=self.import_process.error_traceback or "",
                    identifier=f"mirakl-offer-feed-{self.import_process.remote_import_id}",
                    remote_product=item.remote_product,
                )
