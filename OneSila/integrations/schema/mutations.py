from core.schema.core.mutations import type, delete, create
from integrations.schema.types.input import PublicIssueRequestInput
from integrations.schema.types.types import IntegrationType, PublicIssueRequestType


@type(name="Mutation")
class IntegrationsMutation:
    delete_integration: IntegrationType = delete()
    create_public_issue_request: PublicIssueRequestType = create(PublicIssueRequestInput)
