from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.amazon.schema.types.types import (
    AmazonSalesChannelType,
    AmazonPropertyType,
    AmazonPropertySelectValueType,
)


@type(name="Query")
class AmazonSalesChannelsQuery:
    amazon_channel: AmazonSalesChannelType = node()
    amazon_channels: DjangoListConnection[AmazonSalesChannelType] = connection()

    amazon_property: AmazonPropertyType = node()
    amazon_properties: DjangoListConnection[AmazonPropertyType] = connection()

    amazon_property_select_value: AmazonPropertySelectValueType = node()
    amazon_property_select_values: DjangoListConnection[AmazonPropertySelectValueType] = connection()