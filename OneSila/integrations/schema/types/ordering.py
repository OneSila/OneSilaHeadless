from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from integrations.models import Integration


@order(Integration)
class IntegrationOrder:
    id: auto
    hostname: auto
    active: auto
    created_at: auto
