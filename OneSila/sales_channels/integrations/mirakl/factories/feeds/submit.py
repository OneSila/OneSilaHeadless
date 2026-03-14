from __future__ import annotations

from pathlib import Path

from django.utils import timezone

from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.models import SalesChannelFeed


class MiraklProductFeedSubmitFactory(GetMiraklAPIMixin):
    """Submit a generated Mirakl product feed file."""

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel

    def run(self):
        if not self.feed.file:
            raise ValueError("Feed file is missing.")

        with self.feed.file.open("rb") as file_handle:
            response = self.mirakl_post_multipart(
                path="/api/products/imports",
                files={
                    "file": (
                        Path(self.feed.file.name).name,
                        file_handle,
                        "text/csv",
                    )
                },
                expected_statuses={200, 201, 202},
            )

        remote_import_id = str(response.get("import_id") or response.get("id") or "")
        raw_data = dict(self.feed.raw_data or {})
        raw_data["product_submit_response"] = response
        raw_data["product_import_succeeded"] = False
        self.feed.status = SalesChannelFeed.STATUS_SUBMITTED
        self.feed.stage = self.feed.STAGE_PRODUCT
        self.feed.remote_id = remote_import_id
        self.feed.product_remote_id = remote_import_id
        self.feed.last_submitted_at = timezone.now()
        self.feed.raw_data = raw_data
        self.feed.save(
            update_fields=[
                "status",
                "stage",
                "remote_id",
                "product_remote_id",
                "last_submitted_at",
                "raw_data",
            ]
        )
        return self.feed


class MiraklOfferSubmitFactory(GetMiraklAPIMixin):
    """Submit OF24 offer updates for a Mirakl feed."""

    def __init__(self, *, feed, offers: list[dict]) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel
        self.offers = offers

    def run(self):
        if not self.offers:
            return None

        response = self.mirakl_post(
            path="/api/offers",
            payload={"offers": self.offers},
            expected_statuses={200, 201, 202},
        )
        remote_import_id = str(response.get("import_id") or response.get("id") or "")
        raw_data = dict(self.feed.raw_data or {})
        raw_data["offer_submit_response"] = response
        raw_data["offer_import_succeeded"] = False
        self.feed.stage = self.feed.STAGE_OFFER
        self.feed.status = SalesChannelFeed.STATUS_SUBMITTED
        self.feed.remote_id = remote_import_id
        self.feed.offer_remote_id = remote_import_id
        self.feed.last_submitted_at = timezone.now()
        self.feed.raw_data = raw_data
        self.feed.save(
            update_fields=[
                "stage",
                "status",
                "remote_id",
                "offer_remote_id",
                "last_submitted_at",
                "raw_data",
            ]
        )
        return self.feed
