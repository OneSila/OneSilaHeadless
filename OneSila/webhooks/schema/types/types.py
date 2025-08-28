from typing import Optional

from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from webhooks.models import (
    WebhookIntegration,
    WebhookOutbox,
    WebhookDelivery,
    WebhookDeliveryAttempt,
)

from .filters import (
    WebhookIntegrationFilter,
    WebhookOutboxFilter,
    WebhookDeliveryFilter,
    WebhookDeliveryAttemptFilter,
)
from .ordering import (
    WebhookIntegrationOrder,
    WebhookOutboxOrder,
    WebhookDeliveryOrder,
    WebhookDeliveryAttemptOrder,
)


@type(
    WebhookIntegration,
    filters=WebhookIntegrationFilter,
    order=WebhookIntegrationOrder,
    pagination=True,
    fields="__all__",
)
class WebhookIntegrationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(
    WebhookOutbox,
    filters=WebhookOutboxFilter,
    order=WebhookOutboxOrder,
    pagination=True,
    fields="__all__",
)
class WebhookOutboxType(relay.Node, GetQuerysetMultiTenantMixin):
    webhook_integration: Optional[WebhookIntegrationType]


@type(
    WebhookDelivery,
    filters=WebhookDeliveryFilter,
    order=WebhookDeliveryOrder,
    pagination=True,
    fields="__all__",
)
class WebhookDeliveryType(relay.Node, GetQuerysetMultiTenantMixin):
    outbox: Optional[WebhookOutboxType]
    webhook_integration: Optional[WebhookIntegrationType]


@type(
    WebhookDeliveryAttempt,
    filters=WebhookDeliveryAttemptFilter,
    order=WebhookDeliveryAttemptOrder,
    pagination=True,
    fields="__all__",
)
class WebhookDeliveryAttemptType(relay.Node, GetQuerysetMultiTenantMixin):
    delivery: Optional[WebhookDeliveryType]
