from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, strawberry_type, field
from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.integrations.ebay.schema.types.filters import EbaySalesChannelFilter
from sales_channels.integrations.ebay.schema.types.ordering import EbaySalesChannelOrder


@strawberry_type
class EbayRedirectUrlType:
    redirect_url: str


@type(EbaySalesChannel, filters=EbaySalesChannelFilter, order=EbaySalesChannelOrder, pagination=True, fields="__all__")
class EbaySalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr
