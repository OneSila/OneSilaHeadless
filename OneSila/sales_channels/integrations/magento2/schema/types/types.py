from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, strawberry_type, field
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.schema.types.filters import MagentoSalesChannelFilter
from sales_channels.integrations.magento2.schema.types.ordering import MagentoSalesChannelOrder

@type(MagentoSalesChannel, filters=MagentoSalesChannelFilter, order=MagentoSalesChannelOrder, pagination=True, fields="__all__")
class MagentoSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr


    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr


@strawberry_type
class MagentoRemoteAttributeType:
    id: str
    attribute_code: str
    name: str
    data: str

@strawberry_type
class MagentoRemoteAttributeSetType:
    id: str
    name: str