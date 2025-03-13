from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from integrations.schema.types.types import IntegrationType


@type(name="Query")
class IntegrationsQuery:
    integration: IntegrationType = node()
    integrations: ListConnectionWithTotalCount[IntegrationType] = connection()