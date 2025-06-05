from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.integrations.woocommerce.schema.types.filters import WoocommerceSalesChannelFilter
from sales_channels.integrations.woocommerce.schema.types.ordering import WoocommerceSalesChannelOrder


@type(WoocommerceSalesChannel, filters=WoocommerceSalesChannelFilter, order=WoocommerceSalesChannelOrder, pagination=True, fields="__all__")
class WoocommerceSalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr
