from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.amazon.schema.types.types import AmazonSalesChannelType


@type(name="Query")
class AmazonSalesChannelsQuery:
    amazon_channel: AmazonSalesChannelType = node()
    amazon_channels: DjangoListConnection[AmazonSalesChannelType] = connection()
