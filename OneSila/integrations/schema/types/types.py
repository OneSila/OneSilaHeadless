from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin
from integrations.models import Integration
from integrations.schema.types.filters import IntegrationFilter
from integrations.schema.types.ordering import IntegrationOrder


@type(Integration, filters=IntegrationFilter, order=IntegrationOrder, pagination=True, fields="__all__")
class IntegrationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass