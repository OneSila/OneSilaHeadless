from sales_channels.integrations.shopify.schema.types.input import ShopifySalesChannelInput, \
    ShopifySalesChannelPartialInput
from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType
from core.schema.core.mutations import create, type, List, update


@type(name="Mutation")
class ShopifySalesChannelMutation:
    create_shopify_sales_channel: ShopifySalesChannelType = create(ShopifySalesChannelInput)
    create_shopify_sales_channels: List[ShopifySalesChannelType] = create(ShopifySalesChannelInput)

    update_shopify_sales_channel: ShopifySalesChannelType = update(ShopifySalesChannelPartialInput)