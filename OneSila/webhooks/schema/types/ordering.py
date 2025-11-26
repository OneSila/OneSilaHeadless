from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from webhooks.models import (
    WebhookIntegration,
    WebhookOutbox,
    WebhookDelivery,
    WebhookDeliveryAttempt,
)


@order(WebhookIntegration)
class WebhookIntegrationOrder:
    id: auto
    topic: auto
    created_at: auto


@order(WebhookOutbox)
class WebhookOutboxOrder:
    id: auto
    created_at: auto


@order(WebhookDelivery)
class WebhookDeliveryOrder:
    id: auto
    status: auto
    attempt: auto
    sent_at: auto


@order(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptOrder:
    id: auto
    number: auto
    sent_at: auto
