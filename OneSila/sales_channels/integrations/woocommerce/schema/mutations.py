from sales_channels.integrations.woocommerce.schema.types.input import WoocommerceSalesChannelInput, WoocommerceSalesChannelPartialInput
from sales_channels.integrations.woocommerce.schema.types.types import WoocommerceSalesChannelType
from core.schema.core.mutations import create, type, List, update


@type(name="Mutation")
class WoocommerceSalesChannelMutation:
    create_woocommerce_sales_channel: WoocommerceSalesChannelType = create(WoocommerceSalesChannelInput)
    create_woocommerce_sales_channels: List[WoocommerceSalesChannelType] = create(WoocommerceSalesChannelInput)

    update_woocommerce_sales_channel: WoocommerceSalesChannelType = update(WoocommerceSalesChannelPartialInput)
