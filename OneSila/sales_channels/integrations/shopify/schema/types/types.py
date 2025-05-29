from typing import Optional

from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, strawberry_type, field
from properties.schema.types.types import PropertyType
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.shopify.schema.types.filters import ShopifySalesChannelFilter
from sales_channels.integrations.shopify.schema.types.ordering import ShopifySalesChannelOrder
from core.schema.core.types.types import strawberry_type


@strawberry_type
class ShopifyRedirectUrlType:
    redirect_url: str


@type(ShopifySalesChannel, filters=ShopifySalesChannelFilter, order=ShopifySalesChannelOrder, pagination=True, fields="__all__")
class ShopifySalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    vendor_property: Optional[PropertyType]

    @field()
    def integration_ptr(self, info) -> str:
        return self.integration_ptr

    @field()
    def saleschannel_ptr(self, info) -> str:
        return self.saleschannel_ptr
