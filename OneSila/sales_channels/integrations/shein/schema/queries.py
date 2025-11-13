"""GraphQL query mixins for the Shein integration."""

from core.schema.core.queries import DjangoListConnection, connection, node, type

from sales_channels.integrations.shein.schema.types.types import (
    SheinCategoryType,
    SheinInternalPropertyOptionType,
    SheinInternalPropertyType,
    SheinProductTypeItemType,
    SheinProductTypeType,
    SheinPropertySelectValueType,
    SheinPropertyType,
    SheinRemoteCurrencyType,
    SheinSalesChannelType,
    SheinSalesChannelViewType,
    SheinSalesChannelImportType,
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

    shein_property: SheinPropertyType = node()
    shein_properties: DjangoListConnection[SheinPropertyType] = connection()

    shein_property_select_value: SheinPropertySelectValueType = node()
    shein_property_select_values: DjangoListConnection[SheinPropertySelectValueType] = connection()

    shein_product_type: SheinProductTypeType = node()
    shein_product_types: DjangoListConnection[SheinProductTypeType] = connection()

    shein_product_type_item: SheinProductTypeItemType = node()
    shein_product_type_items: DjangoListConnection[SheinProductTypeItemType] = connection()

    shein_internal_property: SheinInternalPropertyType = node()
    shein_internal_properties: DjangoListConnection[SheinInternalPropertyType] = connection()

    shein_internal_property_option: SheinInternalPropertyOptionType = node()
    shein_internal_property_options: DjangoListConnection[
        SheinInternalPropertyOptionType
    ] = connection()

    shein_import_process: SheinSalesChannelImportType = node()
    shein_import_processes: DjangoListConnection[
        SheinSalesChannelImportType
    ] = connection()

    shein_category: SheinCategoryType = node()
    shein_categories: DjangoListConnection[SheinCategoryType] = connection()
