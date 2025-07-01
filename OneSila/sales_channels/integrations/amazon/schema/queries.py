from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.amazon.schema.types.types import (
    AmazonSalesChannelType,
    AmazonPropertyType,
    AmazonPropertySelectValueType,
    AmazonProductTypeType,
    AmazonProductTypeItemType,
    AmazonSalesChannelImportType,
    AmazonDefaultUnitConfiguratorType,
)


@type(name="Query")
class AmazonSalesChannelsQuery:
    amazon_channel: AmazonSalesChannelType = node()
    amazon_channels: DjangoListConnection[AmazonSalesChannelType] = connection()

    amazon_property: AmazonPropertyType = node()
    amazon_properties: DjangoListConnection[AmazonPropertyType] = connection()

    amazon_property_select_value: AmazonPropertySelectValueType = node()
    amazon_property_select_values: DjangoListConnection[AmazonPropertySelectValueType] = connection()

    amazon_product_type: AmazonProductTypeType = node()
    amazon_product_types: DjangoListConnection[AmazonProductTypeType] = connection()

    amazon_product_type_item: AmazonProductTypeItemType = node()
    amazon_product_type_items: DjangoListConnection[AmazonProductTypeItemType] = connection()

    amazon_import_process: AmazonSalesChannelImportType = node()
    amazon_import_processes: DjangoListConnection[AmazonSalesChannelImportType] = connection()

    amazon_default_unit_configurator: AmazonDefaultUnitConfiguratorType = node()
    amazon_default_unit_configurators: DjangoListConnection[AmazonDefaultUnitConfiguratorType] = connection()
