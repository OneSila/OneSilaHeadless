from core.schema.core.queries import node, connection, DjangoListConnection, type

from .types.types import (
    WebhookIntegrationType,
    WebhookOutboxType,
    WebhookDeliveryType,
    WebhookDeliveryAttemptType,
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
