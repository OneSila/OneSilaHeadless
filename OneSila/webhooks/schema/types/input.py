from core.schema.core.types.input import NodeInput, input, partial

from webhooks.models import WebhookIntegration, WebhookDelivery


@input(WebhookIntegration, fields="__all__")
class WebhookIntegrationInput:
    pass


@partial(WebhookIntegration, fields="__all__")
class WebhookIntegrationPartialInput(NodeInput):
    pass


@partial(WebhookDelivery, fields="__all__")
class WebhookDeliveryPartialInput(NodeInput):
    pass
