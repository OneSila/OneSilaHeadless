from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType

@type(name="Query")
class ShopifySalesChannelsQuery:
    shopify_channel: ShopifySalesChannelType = node()
    shopify_channels: ListConnectionWithTotalCount[ShopifySalesChannelType] = connection()