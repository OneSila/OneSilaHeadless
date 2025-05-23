from core.schema.core.mutations import type, delete
from integrations.schema.types.types import IntegrationType


@type(name="Mutation")
class IntegrationsMutation:
    delete_integration: IntegrationType = delete()
