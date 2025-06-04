from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, strawberry_type
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.schema.types.filters import AmazonSalesChannelFilter
from sales_channels.integrations.amazon.schema.types.ordering import AmazonSalesChannelOrder


@strawberry_type
class AmazonRedirectUrlType:
    redirect_url: str


@type(AmazonSalesChannel, filters=AmazonSalesChannelFilter, order=AmazonSalesChannelOrder, pagination=True, fields="__all__")
class AmazonSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr
