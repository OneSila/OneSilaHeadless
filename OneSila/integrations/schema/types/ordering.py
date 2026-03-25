from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from integrations.models import Integration, PublicIntegrationType


@order(Integration)
class IntegrationOrder:
    id: auto
    hostname: auto
    active: auto
    created_at: auto


@order(PublicIntegrationType)
class PublicIntegrationTypeOrder:
    id: auto
    key: auto
    type: auto
    subtype: auto
    category: auto
    active: auto
    is_beta: auto
    supports_open_ai_product_feed: auto
    sort_order: auto
    created_at: auto
