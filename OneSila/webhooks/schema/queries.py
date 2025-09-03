from core.schema.core.queries import (
    node,
    connection,
    DjangoListConnection,
    type,
    field,
    Info,
)
from statistics import quantiles, median
from typing import Optional
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
from strawberry.relay import from_base64
from django.db.models import Count, Avg, Q, Case, When, Value, CharField, F
from django.db.models.functions import (
    TruncHour,
    TruncDay,
    TruncWeek,
    ExtractWeekDay,
    ExtractHour,
)
from strawberry_django.filters import apply as apply_filters
from core.schema.core.helpers import get_multi_tenant_company

from webhooks.models import WebhookDelivery, WebhookIntegration
from .types.reports import (
    WebhookReportsKPIType,
    WebhookReportsSeriesType,
    DeliveryOutcomeBucket,
    LatencyBucket,
    TopicBreakdown,
    ResponseCodeBreakdown,
    RetriesDistribution,
    HeatmapEntry,
    TopOffender,
    QueuePressureEntry,
    WebhookDeliveryStatsType,
)
from .types.input import WebhookIntegrationPartialInput
from .types.filters import WebhookDeliveryFilter

from .types.types import (
    WebhookIntegrationType,
    WebhookOutboxType,
    WebhookDeliveryType,
    WebhookDeliveryAttemptType,
)


def _decode_id(global_id: str) -> int:
    _, pk = from_base64(global_id)
    return pk


def _apply_filters(
    qs,
    integration: WebhookIntegrationPartialInput,
    time_from: datetime,
    time_to: datetime,
    topic: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
):
    qs = qs.filter(
        webhook_integration_id=_decode_id(integration.id),
        created_at__gte=time_from,
        created_at__lte=time_to,
    ).select_related("outbox")
    if topic:
        qs = qs.filter(outbox__topic=topic)
    if action:
        qs = qs.filter(outbox__action=action)
    if status:
        qs = qs.filter(status=status)
    return qs


def webhook_reports_kpi_resolver(
    info: Info,
    integration: WebhookIntegrationPartialInput,
    time_from: datetime,
    time_to: datetime,
    topic: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
) -> WebhookReportsKPIType:
    qs = _apply_filters(
        WebhookDelivery.objects.all(), integration, time_from, time_to, topic, action, status
    )

    total = qs.count()
    delivered = qs.filter(status=WebhookDelivery.DELIVERED).count()
    failed = qs.filter(status=WebhookDelivery.FAILED).count()
    success_rate = delivered / total * 100 if total else 0.0

    latencies = list(
        qs.filter(response_ms__isnull=False).values_list("response_ms", flat=True)
    )
    latencies.sort()
    if latencies:
        if len(latencies) == 1:
            p50 = p95 = p99 = latencies[0]
        else:
            qs_percentiles = quantiles(latencies, n=100)
            p50 = qs_percentiles[49]
            p95 = qs_percentiles[94]
            p99 = qs_percentiles[98]
    else:
        p50 = p95 = p99 = 0

    rate_429 = qs.filter(response_code=429).count() / total * 100 if total else 0.0
    rate_5xx = (
        qs.filter(response_code__gte=500, response_code__lt=600).count() / total * 100
        if total
        else 0.0
    )
    avg_attempts = qs.aggregate(avg_attempts=Avg("attempt"))["avg_attempts"] or 0.0
    avg_latency = (
        qs.filter(response_ms__isnull=False).aggregate(avg_latency=Avg("response_ms"))["avg_latency"]
        or 0.0
    )

    return WebhookReportsKPIType(
        deliveries=total,
        delivered=delivered,
        failed=failed,
        success_rate=success_rate,
        p50_latency=int(p50),
        p95_latency=int(p95),
        p99_latency=int(p99),
        rate_429=rate_429,
        rate_5xx=rate_5xx,
        avg_attempts=avg_attempts,
        avg_solve_ms=int(avg_latency),
    )


def webhook_reports_series_resolver(
    info: Info,
    integration: WebhookIntegrationPartialInput,
    time_from: datetime,
    time_to: datetime,
    topic: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    bucket: str = "day",
) -> WebhookReportsSeriesType:
    qs = _apply_filters(
        WebhookDelivery.objects.all(), integration, time_from, time_to, topic, action, status
    )

    trunc_map = {
        "hour": TruncHour,
        "week": TruncWeek,
        "day": TruncDay,
    }
    trunc = trunc_map.get(bucket, TruncDay)("created_at")

    delivery_qs = (
        qs.annotate(ts=trunc)
        .values("ts")
        .annotate(
            delivered=Count("id", filter=Q(status=WebhookDelivery.DELIVERED)),
            failed=Count("id", filter=Q(status=WebhookDelivery.FAILED)),
            pending=Count("id", filter=Q(status=WebhookDelivery.PENDING)),
            sending=Count("id", filter=Q(status=WebhookDelivery.SENDING)),
        )
        .order_by("ts")
    )
    delivery_outcome_buckets = [
        DeliveryOutcomeBucket(
            timestamp=entry["ts"],
            delivered=entry["delivered"],
            failed=entry["failed"],
            pending=entry["pending"],
            sending=entry["sending"],
        )
        for entry in delivery_qs
    ]

    latency_dict: dict = defaultdict(list)
    for item in (
        qs.filter(response_ms__isnull=False)
        .annotate(ts=trunc)
        .values("ts", "response_ms")
        .order_by("ts")
    ):
        latency_dict[item["ts"]].append(item["response_ms"])

    latency_buckets = []
    for ts in sorted(latency_dict):
        values = sorted(latency_dict[ts])
        if len(values) == 1:
            p50 = p95 = values[0]
        else:
            qs_percentiles = quantiles(values, n=100)
            p50 = qs_percentiles[49]
            p95 = qs_percentiles[94]
        latency_buckets.append(LatencyBucket(timestamp=ts, p50=int(p50), p95=int(p95)))

    topic_qs = (
        qs.annotate(topic=F("outbox__topic"))
        .values("topic")
        .annotate(
            deliveries=Count("id"),
            delivered=Count("id", filter=Q(status=WebhookDelivery.DELIVERED)),
            failed=Count("id", filter=Q(status=WebhookDelivery.FAILED)),
        )
        .order_by("-deliveries")
    )
    topics_breakdown = [
        TopicBreakdown(
            topic=entry["topic"],
            deliveries=entry["deliveries"],
            delivered=entry["delivered"],
            failed=entry["failed"],
            success_rate=(
                entry["delivered"] / entry["deliveries"] * 100 if entry["deliveries"] else 0
            ),
        )
        for entry in topic_qs
    ]

    code_qs = (
        qs.annotate(
            code_bucket=Case(
                When(response_code=429, then=Value("429")),
                When(response_code__gte=200, response_code__lt=300, then=Value("2xx")),
                When(response_code__gte=400, response_code__lt=500, then=Value("4xx")),
                When(response_code__gte=500, response_code__lt=600, then=Value("5xx")),
                default=Value("timeout"),
                output_field=CharField(),
            )
        )
        .values("code_bucket")
        .annotate(count=Count("id"))
    )
    response_codes_breakdown = [
        ResponseCodeBreakdown(code_bucket=entry["code_bucket"], count=entry["count"])
        for entry in code_qs
    ]

    retries_distribution = [
        RetriesDistribution(attempts=entry["attempt"], count=entry["count"])
        for entry in qs.values("attempt").annotate(count=Count("id")).order_by("attempt")
    ]

    heatmap_dict: dict = defaultdict(lambda: {"failures": 0, "latencies": []})
    for d in qs.only("created_at", "status", "response_ms"):
        weekday = d.created_at.isoweekday()
        hour = d.created_at.hour
        key = (weekday, hour)
        if d.status == WebhookDelivery.FAILED:
            heatmap_dict[key]["failures"] += 1
        if d.response_ms is not None:
            heatmap_dict[key]["latencies"].append(d.response_ms)

    heatmap = []
    for (weekday, hour), data in heatmap_dict.items():
        med_latency = int(median(data["latencies"])) if data["latencies"] else 0
        heatmap.append(
            HeatmapEntry(
                weekday=weekday,
                hour=hour,
                failures=data["failures"],
                median_latency=med_latency,
            )
        )
    heatmap.sort(key=lambda x: (x.weekday, x.hour))

    top_qs = (
        qs.values("webhook_integration_id")
        .annotate(
            deliveries=Count("id"),
            failed=Count("id", filter=Q(status=WebhookDelivery.FAILED)),
        )
        .order_by("-failed")[:10]
    )
    top_offenders = []
    for entry in top_qs:
        integration_obj = WebhookIntegration.objects.get(pk=entry["webhook_integration_id"])
        lat_values = list(
            qs.filter(webhook_integration_id=integration_obj.pk, response_ms__isnull=False)
            .values_list("response_ms", flat=True)
        )
        lat_values.sort()
        if lat_values:
            if len(lat_values) == 1:
                p95 = lat_values[0]
            else:
                p95 = quantiles(lat_values, n=100)[94]
        else:
            p95 = 0
        hostname = urlparse(integration_obj.url).hostname or ""
        failure_rate = (
            entry["failed"] / entry["deliveries"] * 100 if entry["deliveries"] else 0
        )
        top_offenders.append(
            TopOffender(
                integration_id=integration_obj.pk,
                integration_hostname=hostname,
                failure_rate=failure_rate,
                latency_p95=int(p95),
            )
        )

    queue_qs = (
        qs.annotate(ts=trunc)
        .values("ts")
        .annotate(pending=Count("id", filter=Q(status=WebhookDelivery.PENDING)))
        .order_by("ts")
    )
    queue_pressure = [
        QueuePressureEntry(timestamp=entry["ts"], pending=entry["pending"])
        for entry in queue_qs
    ]

    return WebhookReportsSeriesType(
        delivery_outcome_buckets=delivery_outcome_buckets,
        latency_buckets=latency_buckets,
        topics_breakdown=topics_breakdown,
        response_codes_breakdown=response_codes_breakdown,
        retries_distribution=retries_distribution,
        heatmap=heatmap,
        top_offenders=top_offenders,
        queue_pressure=queue_pressure,
    )


def webhook_delivery_stats_resolver(
    info: Info,
    filters: Optional[WebhookDeliveryFilter] = None,
) -> WebhookDeliveryStatsType:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    qs = WebhookDelivery.objects.filter(multi_tenant_company=multi_tenant_company)
    qs = apply_filters(filters, qs, info)

    total = qs.count()
    delivered = qs.filter(status=WebhookDelivery.DELIVERED).count()
    failed = qs.filter(status=WebhookDelivery.FAILED).count()
    success_rate = delivered / total * 100 if total else 0.0

    latencies = list(
        qs.filter(response_ms__isnull=False).values_list("response_ms", flat=True)
    )
    latencies.sort()
    if latencies:
        median_latency = int(median(latencies))
        if len(latencies) == 1:
            p95_latency = p99_latency = latencies[0]
        else:
            qs_percentiles = quantiles(latencies, n=100)
            p95_latency = int(qs_percentiles[94])
            p99_latency = int(qs_percentiles[98])
    else:
        median_latency = p95_latency = p99_latency = 0

    rate_429 = qs.filter(response_code=429).count() / total * 100 if total else 0.0
    rate_5xx = (
        qs.filter(response_code__gte=500, response_code__lt=600).count() / total * 100
        if total
        else 0.0
    )
    avg_attempts = qs.aggregate(avg_attempts=Avg("attempt"))["avg_attempts"] or 0.0
    avg_response_ms = (
        qs.filter(response_ms__isnull=False).aggregate(avg_response_ms=Avg("response_ms"))["avg_response_ms"]
        or 0.0
    )
    queue_depth = qs.filter(status=WebhookDelivery.PENDING).count()

    return WebhookDeliveryStatsType(
        deliveries=total,
        delivered=delivered,
        failed=failed,
        success_rate=success_rate,
        median_latency=median_latency,
        p95_latency=p95_latency,
        p99_latency=p99_latency,
        rate_429=rate_429,
        rate_5xx=rate_5xx,
        avg_attempts=avg_attempts,
        avg_response_ms=int(avg_response_ms),
        queue_depth=queue_depth,
    )


@type(name="Query")
class WebhooksQuery:
    webhook_integration: WebhookIntegrationType = node()
    webhook_integrations: DjangoListConnection[WebhookIntegrationType] = connection()

    webhook_outbox: WebhookOutboxType = node()
    webhook_outboxes: DjangoListConnection[WebhookOutboxType] = connection()

    webhook_delivery: WebhookDeliveryType = node()
    webhook_deliveries: DjangoListConnection[WebhookDeliveryType] = connection()

    webhook_delivery_attempt: WebhookDeliveryAttemptType = node()
    webhook_delivery_attempts: DjangoListConnection[WebhookDeliveryAttemptType] = connection()

    webhook_delivery_stats: WebhookDeliveryStatsType = field(
        resolver=webhook_delivery_stats_resolver
    )

    webhook_reports_kpi: WebhookReportsKPIType = field(
        resolver=webhook_reports_kpi_resolver
    )
    webhook_reports_series: WebhookReportsSeriesType = field(
        resolver=webhook_reports_series_resolver
    )
