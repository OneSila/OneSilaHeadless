from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.ebay.schema.types.types import (
    EbaySalesChannelType,
    EbayInternalPropertyType,
    EbayProductTypeType,
    EbayProductTypeItemType,
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

    ebay_product_type: EbayProductTypeType = node()
    ebay_product_types: DjangoListConnection[EbayProductTypeType] = connection()

    ebay_product_type_item: EbayProductTypeItemType = node()
    ebay_product_type_items: DjangoListConnection[EbayProductTypeItemType] = connection()

    ebay_internal_property: EbayInternalPropertyType = node()
    ebay_internal_properties: DjangoListConnection[EbayInternalPropertyType] = connection()

    ebay_property_select_value: EbayPropertySelectValueType = node()
    ebay_property_select_values: DjangoListConnection[EbayPropertySelectValueType] = connection()

    ebay_sales_channel_view: EbaySalesChannelViewType = node()
    ebay_sales_channel_views: DjangoListConnection[EbaySalesChannelViewType] = connection()
