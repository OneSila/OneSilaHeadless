from core.schema.core.types.input import NodeInput, input, partial
from integrations.models import PublicIntegrationType, PublicIssueRequest


@partial(PublicIntegrationType, fields="__all__")
class PublicIntegrationTypePartialInput(NodeInput):
    pass


@input(
    PublicIssueRequest,
    fields=("integration_type", "issue", "description", "submission_id", "product_sku"),
)
class PublicIssueRequestInput:
    integration_type: PublicIntegrationTypePartialInput
    pass
