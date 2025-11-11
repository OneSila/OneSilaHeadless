"""GraphQL query mixins for the Shein integration."""

from core.schema.core.queries import DjangoListConnection, connection, node, type

from sales_channels.integrations.shein.schema.types.types import (
    SheinRemoteCurrencyType,
    SheinSalesChannelType,
    SheinSalesChannelViewType,
)


@type(name="Query")
class SheinSalesChannelsQuery:
    """Expose Shein sales channels via Relay connections."""

    shein_channel: SheinSalesChannelType = node()
    shein_channels: DjangoListConnection[SheinSalesChannelType] = connection()

    shein_sales_channel_view: SheinSalesChannelViewType = node()
    shein_sales_channel_views: DjangoListConnection[SheinSalesChannelViewType] = connection()

    shein_remote_currency: SheinRemoteCurrencyType = node()
    shein_remote_currencies: DjangoListConnection[SheinRemoteCurrencyType] = connection()
