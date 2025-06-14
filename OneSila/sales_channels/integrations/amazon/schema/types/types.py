from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, strawberry_type
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
)
from sales_channels.integrations.amazon.schema.types.filters import (
    AmazonSalesChannelFilter,
    AmazonPropertyFilter,
    AmazonPropertySelectValueFilter,
)
from sales_channels.integrations.amazon.schema.types.ordering import (
    AmazonSalesChannelOrder,
    AmazonPropertyOrder,
    AmazonPropertySelectValueOrder,
)


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


@type(
    AmazonProperty,
    filters=AmazonPropertyFilter,
    order=AmazonPropertyOrder,
    pagination=True,
    fields="__all__",
)
class AmazonPropertyType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(
    AmazonPropertySelectValue,
    filters=AmazonPropertySelectValueFilter,
    order=AmazonPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
)
class AmazonPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    pass