from core.schema.core.queries import node, connection, DjangoListConnection, type
from integrations.schema.types.types import (
    IntegrationType,
    PublicIntegrationTypeType,
    PublicIssueCategoryType,
    PublicIssueType,
)


@type(name="Query")
class IntegrationsQuery:
    integration: IntegrationType = node()
    integrations: DjangoListConnection[IntegrationType] = connection()
    public_integration_types: DjangoListConnection[PublicIntegrationTypeType] = connection()
    public_issue_categories: DjangoListConnection[PublicIssueCategoryType] = connection()
    public_issue: PublicIssueType = node()
    public_issues: DjangoListConnection[PublicIssueType] = connection()
