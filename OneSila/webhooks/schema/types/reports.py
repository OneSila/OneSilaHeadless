from datetime import datetime
from typing import List, Optional
from core.schema.core.types.types import strawberry_type


@strawberry_type
class DeliveryOutcomeBucket:
    timestamp: datetime
    delivered: int
    failed: int
    pending: int
    sending: int


@strawberry_type
class LatencyBucket:
    timestamp: datetime
    p50: int
    p95: int


@strawberry_type
class TopicBreakdown:
    topic: str
    deliveries: int
    delivered: int
    failed: int
    success_rate: float


@strawberry_type
class ResponseCodeBreakdown:
    code_bucket: str
    count: int


@strawberry_type
class RetriesDistribution:
    attempts: int
    count: int


@strawberry_type
class HeatmapEntry:
    weekday: int
    hour: int
    failures: int
    median_latency: int


@strawberry_type
class TopOffender:
    integration_id: int
    integration_hostname: str
    failure_rate: float
    latency_p95: int


@strawberry_type
class QueuePressureEntry:
    timestamp: datetime
    pending: int


@strawberry_type
class WebhookReportsSeriesType:
    delivery_outcome_buckets: List[DeliveryOutcomeBucket]
    latency_buckets: List[LatencyBucket]
    topics_breakdown: List[TopicBreakdown]
    response_codes_breakdown: List[ResponseCodeBreakdown]
    retries_distribution: List[RetriesDistribution]
    heatmap: List[HeatmapEntry]
    top_offenders: List[TopOffender]
    queue_pressure: Optional[List[QueuePressureEntry]] = None


@strawberry_type
class WebhookReportsKPIType:
    deliveries: int
    delivered: int
    failed: int
    success_rate: float
    p50_latency: int
    p95_latency: int
    p99_latency: int
    rate_429: float
    rate_5xx: float
    avg_attempts: float
    avg_solve_ms: int


@strawberry_type
class WebhookDeliveryStatsType:
    deliveries: int
    delivered: int
    failed: int
    success_rate: float
    median_latency: int
    p95_latency: int
    p99_latency: int
    rate_429: float
    rate_5xx: float
    avg_attempts: float
    avg_response_ms: int
    queue_depth: int
