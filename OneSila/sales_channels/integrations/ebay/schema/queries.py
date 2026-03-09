from core.schema.core.queries import node, connection, DjangoListConnection, type
from sales_channels.integrations.ebay.schema.types.types import (
    EbayCategoryType,
    EbayProductCategoryType,
    EbayProductStoreCategoryType,
    EbaySalesChannelType,
    EbayStoreCategoryType,
    EbayInternalPropertyType,
    EbayInternalPropertyOptionType,
    EbayProductTypeType,
    EbayProductTypeItemType,
    EbayPropertyType,
    EbayPropertySelectValueType,
    EbaySalesChannelViewType,
    EbaySalesChannelImportType,
    EbayCurrencyType,
    EbayDocumentTypeType,
)


@type(name="Query")
class EbaySalesChannelsQuery:
    ebay_categories: DjangoListConnection[EbayCategoryType] = connection()
    ebay_product_category: EbayProductCategoryType = node()
    ebay_product_categories: DjangoListConnection[EbayProductCategoryType] = connection()
    ebay_store_category: EbayStoreCategoryType = node()
    ebay_store_categories: DjangoListConnection[EbayStoreCategoryType] = connection()
    ebay_product_store_category: EbayProductStoreCategoryType = node()
    ebay_product_store_categories: DjangoListConnection[EbayProductStoreCategoryType] = connection()

    ebay_channel: EbaySalesChannelType = node()
    ebay_channels: DjangoListConnection[EbaySalesChannelType] = connection()

    ebay_property: EbayPropertyType = node()
    ebay_properties: DjangoListConnection[EbayPropertyType] = connection()

    ebay_product_type: EbayProductTypeType = node()
    ebay_product_types: DjangoListConnection[EbayProductTypeType] = connection()
    ebay_product_type_items: DjangoListConnection[EbayProductTypeItemType] = connection()

    ebay_internal_property: EbayInternalPropertyType = node()
    ebay_internal_properties: DjangoListConnection[EbayInternalPropertyType] = connection()

    ebay_internal_property_option: EbayInternalPropertyOptionType = node()
    ebay_internal_property_options: DjangoListConnection[EbayInternalPropertyOptionType] = connection()

    ebay_property_select_value: EbayPropertySelectValueType = node()
    ebay_property_select_values: DjangoListConnection[EbayPropertySelectValueType] = connection()

    ebay_sales_channel_view: EbaySalesChannelViewType = node()
    ebay_sales_channel_views: DjangoListConnection[EbaySalesChannelViewType] = connection()

    ebay_import_process: EbaySalesChannelImportType = node()
    ebay_import_processes: DjangoListConnection[EbaySalesChannelImportType] = connection()

    ebay_currency: EbayCurrencyType = node()
    ebay_currencies: DjangoListConnection[EbayCurrencyType] = connection()

    ebay_document_type: EbayDocumentTypeType = node()
    ebay_document_types: DjangoListConnection[EbayDocumentTypeType] = connection()
