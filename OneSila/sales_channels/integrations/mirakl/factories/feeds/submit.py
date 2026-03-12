from __future__ import annotations

from pathlib import Path

from django.utils import timezone

from imports_exports.models import Import
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannelImport
from sales_channels.models import SalesChannelFeed


class MiraklProductFeedSubmitFactory(GetMiraklAPIMixin):
    """Submit a generated Mirakl product feed file."""

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel

    def run(self) -> MiraklSalesChannelImport:
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
        import_process = MiraklSalesChannelImport.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            type=MiraklSalesChannelImport.TYPE_PRODUCT,
            status=Import.STATUS_PENDING,
            name=f"Mirakl product feed - {self.sales_channel.hostname}",
            feed=self.feed,
            remote_import_id=remote_import_id,
            source_file_name=Path(self.feed.file.name).name,
            raw_response=response,
            summary_data=response,
        )
        self.feed.status = SalesChannelFeed.STATUS_SUBMITTED
        self.feed.remote_id = remote_import_id
        self.feed.last_submitted_at = timezone.now()
        self.feed.save(update_fields=["status", "remote_id", "last_submitted_at"])
        return import_process


class MiraklOfferSubmitFactory(GetMiraklAPIMixin):
    """Submit OF24 offer updates for a Mirakl feed."""

    def __init__(self, *, feed, offers: list[dict]) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel
        self.offers = offers

    def run(self) -> MiraklSalesChannelImport | None:
        if not self.offers:
            return None

        response = self.mirakl_post(
            path="/api/offers",
            payload={"offers": self.offers},
            expected_statuses={200, 201, 202},
        )
        remote_import_id = str(response.get("import_id") or response.get("id") or "")
        return MiraklSalesChannelImport.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            type=MiraklSalesChannelImport.TYPE_OFFER,
            status=Import.STATUS_PENDING,
            name=f"Mirakl offer publish - {self.sales_channel.hostname}",
            feed=self.feed,
            remote_import_id=remote_import_id,
            offer_response=response,
            summary_data=response,
        )
