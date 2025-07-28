from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.ebay.schema.types.types import EbaySalesChannelType


@type(name="Query")
class EbaySalesChannelsQuery:
    ebay_channel: EbaySalesChannelType = node()
    ebay_channels: DjangoListConnection[EbaySalesChannelType] = connection()
