from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, strawberry_type
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
)
from sales_channels.integrations.amazon.schema.types.filters import (
    AmazonSalesChannelFilter,
    AmazonPropertyFilter,
    AmazonPropertySelectValueFilter,
    AmazonProductTypeFilter,
)
from sales_channels.integrations.amazon.schema.types.ordering import (
    AmazonSalesChannelOrder,
    AmazonPropertyOrder,
    AmazonPropertySelectValueOrder,
    AmazonProductTypeOrder,
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
    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    AmazonPropertySelectValue,
    filters=AmazonPropertySelectValueFilter,
    order=AmazonPropertySelectValueOrder,
    pagination=True,
    fields="__all__",
)
class AmazonPropertySelectValueType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely


@type(
    AmazonProductType,
    filters=AmazonProductTypeFilter,
    order=AmazonProductTypeOrder,
    pagination=True,
    fields="__all__",
)
class AmazonProductTypeType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def mapped_locally(self, info) -> bool:
        return self.mapped_locally

    @field()
    def mapped_remotely(self, info) -> bool:
        return self.mapped_remotely

