from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, strawberry_type, field
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.shopify.schema.types.filters import ShopifySalesChannelFilter
from sales_channels.integrations.shopify.schema.types.ordering import ShopifySalesChannelOrder

@type(ShopifySalesChannel, filters=ShopifySalesChannelFilter, order=ShopifySalesChannelOrder, pagination=True, fields="__all__")
class ShopifySalesChannelType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
