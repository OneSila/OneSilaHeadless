from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.amazon.schema.types.types import (
    AmazonSalesChannelType,
    AmazonPropertyType,
    AmazonPropertySelectValueType,
    AmazonProductType,
    AmazonProductPropertyType,
    AmazonProductTypeType,
    AmazonProductTypeItemType,
    AmazonSalesChannelImportType,
    AmazonDefaultUnitConfiguratorType,
    AmazonRemoteLogType,
    AmazonSalesChannelViewType,
    AmazonProductIssueType,
)


@type(name="Query")
class AmazonSalesChannelsQuery:
    amazon_channel: AmazonSalesChannelType = node()
    amazon_channels: DjangoListConnection[AmazonSalesChannelType] = connection()

    amazon_property: AmazonPropertyType = node()
    amazon_properties: DjangoListConnection[AmazonPropertyType] = connection()

    amazon_property_select_value: AmazonPropertySelectValueType = node()
    amazon_property_select_values: DjangoListConnection[AmazonPropertySelectValueType] = connection()

    amazon_product_property: AmazonProductPropertyType = node()
    amazon_product_properties: DjangoListConnection[AmazonProductPropertyType] = connection()

    amazon_product: AmazonProductType = node()
    amazon_products: DjangoListConnection[AmazonProductType] = connection()

    amazon_product_type: AmazonProductTypeType = node()
    amazon_product_types: DjangoListConnection[AmazonProductTypeType] = connection()

    amazon_product_type_item: AmazonProductTypeItemType = node()
    amazon_product_type_items: DjangoListConnection[AmazonProductTypeItemType] = connection()

    amazon_import_process: AmazonSalesChannelImportType = node()
    amazon_import_processes: DjangoListConnection[AmazonSalesChannelImportType] = connection()

    amazon_default_unit_configurator: AmazonDefaultUnitConfiguratorType = node()
    amazon_default_unit_configurators: DjangoListConnection[AmazonDefaultUnitConfiguratorType] = connection()

    amazon_remote_log: AmazonRemoteLogType = node()
    amazon_remote_logs: DjangoListConnection[AmazonRemoteLogType] = connection()

    amazon_product_issue: AmazonProductIssueType = node()
    amazon_product_issues: DjangoListConnection[AmazonProductIssueType] = connection()

    amazon_channel_view: AmazonSalesChannelViewType = node()
    amazon_channel_views: DjangoListConnection[AmazonSalesChannelViewType] = connection()
