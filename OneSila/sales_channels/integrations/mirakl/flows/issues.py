from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.sales_channels import MiraklProductIssuesFetchFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannel


def refresh_mirakl_product_issues_differential(*, sales_channel_id: int | None = None) -> list[dict]:
    queryset = MiraklSalesChannel.objects.filter(active=True)
    if sales_channel_id is not None:
        queryset = queryset.filter(id=sales_channel_id)
    else:
        cutoff = timezone.now() - timedelta(minutes=30)
        queryset = queryset.filter(
            last_full_fetch__isnull=False,
        ).filter(
            Q(last_differential_issues_fetch__isnull=True)
            | Q(last_differential_issues_fetch__lt=cutoff)
        )

    results: list[dict] = []
    for sales_channel in queryset.order_by("id").iterator():
        results.append(
            MiraklProductIssuesFetchFactory(
                sales_channel=sales_channel,
                mode=MiraklProductIssuesFetchFactory.MODE_DIFFERENTIAL,
            ).run()
        )
    return results


def refresh_mirakl_product_issues_full(*, sales_channel_id: int | None = None) -> list[dict]:
    queryset = MiraklSalesChannel.objects.filter(active=True)
    if sales_channel_id is not None:
        queryset = queryset.filter(id=sales_channel_id)
    else:
        cutoff = timezone.now() - timedelta(hours=12)
        queryset = queryset.filter(Q(last_full_fetch__isnull=True) | Q(last_full_fetch__lt=cutoff))

    results: list[dict] = []
    for sales_channel in queryset.order_by("id").iterator():
        results.append(
            MiraklProductIssuesFetchFactory(
                sales_channel=sales_channel,
                mode=MiraklProductIssuesFetchFactory.MODE_FULL,
            ).run()
        )
    return results
