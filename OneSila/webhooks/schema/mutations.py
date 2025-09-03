from core.schema.core.mutations import create, update, delete, type, List
from core.schema.core.extensions import default_extensions
import strawberry_django
from strawberry import Info

from .types.types import WebhookIntegrationType, WebhookDeliveryType
from .types.input import (
    WebhookIntegrationInput,
    WebhookIntegrationPartialInput,
    WebhookDeliveryPartialInput,
)


@type(name="Mutation")
class WebhooksMutation:
    create_webhook_integration: WebhookIntegrationType = create(WebhookIntegrationInput)
    create_webhook_integrations: List[WebhookIntegrationType] = create(WebhookIntegrationInput)
    update_webhook_integration: WebhookIntegrationType = update(WebhookIntegrationPartialInput)
    delete_webhook_integration: WebhookIntegrationType = delete()
    delete_webhook_integrations: List[WebhookIntegrationType] = delete()

    @strawberry_django.mutation(
        handle_django_errors=False, extensions=default_extensions
    )
    def retry_webhook_delivery(
        self, instance: WebhookDeliveryPartialInput, info: Info
    ) -> WebhookDeliveryType:
        from webhooks.factories import SendWebhookDeliveryFactory
        from webhooks.models import WebhookDelivery

        delivery = WebhookDelivery.objects.select_related("webhook_integration", "outbox").get(
            id=instance.id.node_id
        )
        factory = SendWebhookDeliveryFactory(
            outbox_id=delivery.outbox_id, delivery_id=delivery.pk
        )
        factory.run()
        delivery.refresh_from_db()
        return delivery

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def regenerate_webhook_integration_secret(
        self, instance: WebhookIntegrationPartialInput, info: Info
    ) -> WebhookIntegrationType:
        from webhooks.models import WebhookIntegration

        integration = WebhookIntegration.objects.get(id=instance.id.node_id)
        integration.regenerate_secret()
        return integration
