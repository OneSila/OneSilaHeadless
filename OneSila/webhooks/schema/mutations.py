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
        from webhooks.models import WebhookDelivery

        print(f"Retrying webhook delivery {instance.id.node_id}")
        return WebhookDelivery.objects.get(id=instance.id.node_id)

    @strawberry_django.mutation(
        handle_django_errors=True, extensions=default_extensions
    )
    def regenerate_webhook_integration_secret(
        self, instance: WebhookIntegrationPartialInput, info: Info
    ) -> WebhookIntegrationType:
        from webhooks.models import WebhookIntegration

        integration = WebhookIntegration.objects.get(id=instance.id.node_id)
        integration.regenerate_secret()
        return integration
