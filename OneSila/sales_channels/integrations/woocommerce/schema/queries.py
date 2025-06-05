from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.woocommerce.schema.types.types import WoocommerceSalesChannelType


@type(name="Query")
class WoocommerceSalesChannelsQuery:
    woocommerce_channel: WoocommerceSalesChannelType = node()
    woocommerce_channels: DjangoListConnection[WoocommerceSalesChannelType] = connection()
