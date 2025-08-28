from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from webhooks.models import (
    WebhookIntegration,
    WebhookOutbox,
    WebhookDelivery,
    WebhookDeliveryAttempt,
)


@filter(WebhookIntegration)
class WebhookIntegrationFilter(SearchFilterMixin):
    id: auto
    topic: auto
    version: auto
    url: auto
    mode: auto
    retention_policy: auto


@filter(WebhookOutbox)
class WebhookOutboxFilter(SearchFilterMixin):
    id: auto
    webhook_integration: Optional[WebhookIntegrationFilter]
    topic: auto
    action: auto
    subject_type: auto
    subject_id: auto


@filter(WebhookDelivery)
class WebhookDeliveryFilter(SearchFilterMixin):
    id: auto
    outbox: Optional[WebhookOutboxFilter]
    webhook_integration: Optional[WebhookIntegrationFilter]
    status: auto
    attempt: auto
    response_code: auto


@filter(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptFilter(SearchFilterMixin):
    id: auto
    delivery: Optional[WebhookDeliveryFilter]
    number: auto
    response_code: auto
