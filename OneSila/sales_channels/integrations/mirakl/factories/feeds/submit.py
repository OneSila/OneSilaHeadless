from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.models import SalesChannelFeed


class MiraklProductFeedSubmitFactory(GetMiraklAPIMixin):
    """Submit a generated Mirakl feed file through the combined offer import endpoint."""

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel

    def run(self):
        if not self.feed.file:
            raise ValueError("Feed file is missing.")

        if settings.DEBUG:
            raw_data = dict(self.feed.raw_data or {})
            raw_data["product_submit_skipped"] = True
            raw_data["product_submit_skip_reason"] = "Skipped OF01 upload because settings.DEBUG is True."
            self.feed.__class__.objects.filter(id=self.feed.id).update(
                status=SalesChannelFeed.STATUS_SUCCESS,
                stage=self.feed.STAGE_PRODUCT,
                raw_data=raw_data,
                updated_at=timezone.now(),
            )
            self.feed.status = SalesChannelFeed.STATUS_SUCCESS
            self.feed.stage = self.feed.STAGE_PRODUCT
            self.feed.raw_data = raw_data
            self._mark_items_success_for_debug_skip()
            return self.feed

        with self.feed.file.open("rb") as file_handle:
            response = self.mirakl_post_multipart(
                path="/api/offers/imports",
                payload={
                    "import_mode": "NORMAL",
                    "operator_format": "true",
                    "with_products": "true",
                },
                files={
                    "file": (
                        Path(self.feed.file.name).name,
                        file_handle,
                        "text/csv",
                    )
                },
                expected_statuses={200, 201, 202},
            )

        offer_import_id = str(response.get("import_id") or response.get("id") or "")
        product_import_id = str(response.get("product_import_id") or "")
        raw_data = dict(self.feed.raw_data or {})
        raw_data["product_submit_response"] = response
        self.feed.status = SalesChannelFeed.STATUS_SUBMITTED
        self.feed.stage = self.feed.STAGE_PRODUCT
        self.feed.remote_id = product_import_id
        self.feed.product_remote_id = product_import_id
        self.feed.offer_import_remote_id = offer_import_id
        self.feed.last_submitted_at = timezone.now()
        self.feed.raw_data = raw_data
        self.feed.save(
            update_fields=[
                "status",
                "stage",
                "remote_id",
                "product_remote_id",
                "offer_import_remote_id",
                "last_submitted_at",
                "raw_data",
            ]
        )
        return self.feed

    def _mark_items_success_for_debug_skip(self) -> None:
        from sales_channels.integrations.mirakl.models import MiraklSalesChannelFeedItem

        for item in MiraklSalesChannelFeedItem.objects.filter(feed=self.feed).select_related("remote_product"):
            item.status = MiraklSalesChannelFeedItem.STATUS_SUCCESS
            item.error_message = ""
            item.save(update_fields=["status", "error_message"])

            remote_product = item.remote_product
            if remote_product is None:
                continue
            remote_product.refresh_status(
                override_status=remote_product.STATUS_COMPLETED,
            )
