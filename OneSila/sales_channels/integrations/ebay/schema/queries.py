from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.ebay.schema.types.types import (
    EbaySalesChannelType,
    EbayPropertyType,
    EbayPropertySelectValueType,
    EbaySalesChannelViewType,
)


@type(name="Query")
class EbaySalesChannelsQuery:
    ebay_channel: EbaySalesChannelType = node()
    ebay_channels: DjangoListConnection[EbaySalesChannelType] = connection()

    ebay_property: EbayPropertyType = node()
    ebay_properties: DjangoListConnection[EbayPropertyType] = connection()

    ebay_property_select_value: EbayPropertySelectValueType = node()
    ebay_property_select_values: DjangoListConnection[EbayPropertySelectValueType] = connection()

    ebay_channel_view: EbaySalesChannelViewType = node()
    ebay_channel_views: DjangoListConnection[EbaySalesChannelViewType] = connection()
