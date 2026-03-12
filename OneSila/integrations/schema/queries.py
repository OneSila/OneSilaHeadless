from core.schema.core.queries import node, connection, DjangoListConnection, type
from integrations.schema.types.types import IntegrationType, PublicIntegrationTypeType


@type(name="Query")
class IntegrationsQuery:
    integration: IntegrationType = node()
    integrations: DjangoListConnection[IntegrationType] = connection()
    public_integration_types: DjangoListConnection[PublicIntegrationTypeType] = connection()
