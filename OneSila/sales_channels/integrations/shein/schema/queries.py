"""GraphQL query mixins for the Shein integration."""

from core.schema.core.queries import DjangoListConnection, connection, node, type

from sales_channels.integrations.shein.schema.types.types import SheinSalesChannelType


@type(name="Query")
class SheinSalesChannelsQuery:
    """Expose Shein sales channels via Relay connections."""

    shein_channel: SheinSalesChannelType = node()
    shein_channels: DjangoListConnection[SheinSalesChannelType] = connection()
