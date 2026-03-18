from __future__ import annotations

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from sales_channels.integrations.mirakl.factories.sales_channels import MiraklProductIssuesFetchFactory
from sales_channels.integrations.mirakl.models import MiraklSalesChannel

logger = logging.getLogger(__name__)


def refresh_mirakl_product_issues_differential(*, sales_channel_id: int | None = None) -> list[dict]:
    queryset = MiraklSalesChannel.objects.filter(active=True)
    if sales_channel_id is not None:
        queryset = queryset.filter(id=sales_channel_id)
    else:
        cutoff = timezone.now() - timedelta(minutes=30)
        queryset = queryset.filter(
            last_full_issues_fetch__isnull=False,
        ).filter(
            Q(last_differential_issues_fetch__isnull=True)
            | Q(last_differential_issues_fetch__lt=cutoff)
        )

    results: list[dict] = []
    for sales_channel in queryset.order_by("id").iterator():
        if not sales_channel.connected:
            logger.info(
                "Skipping Mirakl differential issues fetch for channel %s because it is not connected.",
                sales_channel.id,
            )
            continue
        try:
            results.append(
                MiraklProductIssuesFetchFactory(
                    sales_channel=sales_channel,
                    mode=MiraklProductIssuesFetchFactory.MODE_DIFFERENTIAL,
                ).run()
            )
        except Exception:
            logger.exception(
                "Mirakl differential issues fetch failed for sales_channel_id=%s",
                sales_channel.id,
            )
    return results


def refresh_mirakl_product_issues_full(*, sales_channel_id: int | None = None) -> list[dict]:
    queryset = MiraklSalesChannel.objects.filter(active=True)
    if sales_channel_id is not None:
        queryset = queryset.filter(id=sales_channel_id)
    else:
        cutoff = timezone.now() - timedelta(hours=12)
        queryset = queryset.filter(Q(last_full_issues_fetch__isnull=True) | Q(last_full_issues_fetch__lt=cutoff))

    results: list[dict] = []
    for sales_channel in queryset.order_by("id").iterator():
        if not sales_channel.connected:
            logger.info(
                "Skipping Mirakl full issues fetch for channel %s because it is not connected.",
                sales_channel.id,
            )
            continue
        try:
            results.append(
                MiraklProductIssuesFetchFactory(
                    sales_channel=sales_channel,
                    mode=MiraklProductIssuesFetchFactory.MODE_FULL,
                ).run()
            )
        except Exception:
            logger.exception(
                "Mirakl full issues fetch failed for sales_channel_id=%s",
                sales_channel.id,
            )
    return results
