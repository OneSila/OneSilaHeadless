from core.schema.core.queries import DjangoListConnection, connection, node, type

from sales_channels.integrations.mirakl.schema.types.types import (
    MiraklCategoryType,
    MiraklDocumentTypeType,
    MiraklEanCodeType,
    MiraklInternalPropertyOptionType,
    MiraklInternalPropertyType,
    MiraklPriceType,
    MiraklProductCategoryType,
    MiraklProductContentType,
    MiraklProductType,
    MiraklProductTypeItemType,
    MiraklPropertyApplicabilityType,
    MiraklPropertySelectValueType,
    MiraklPropertyType,
    MiraklRemoteCurrencyType,
    MiraklRemoteLanguageType,
    MiraklSalesChannelImportType,
    MiraklSalesChannelType,
    MiraklSalesChannelViewType,
)


@type(name="Query")
class MiraklSalesChannelsQuery:
    mirakl_channel: MiraklSalesChannelType = node()
    mirakl_channels: DjangoListConnection[MiraklSalesChannelType] = connection()

    mirakl_sales_channel_view: MiraklSalesChannelViewType = node()
    mirakl_sales_channel_views: DjangoListConnection[MiraklSalesChannelViewType] = connection()

    mirakl_remote_currency: MiraklRemoteCurrencyType = node()
    mirakl_remote_currencies: DjangoListConnection[MiraklRemoteCurrencyType] = connection()

    mirakl_remote_language: MiraklRemoteLanguageType = node()
    mirakl_remote_languages: DjangoListConnection[MiraklRemoteLanguageType] = connection()

    mirakl_internal_property: MiraklInternalPropertyType = node()
    mirakl_internal_properties: DjangoListConnection[MiraklInternalPropertyType] = connection()

    mirakl_internal_property_option: MiraklInternalPropertyOptionType = node()
    mirakl_internal_property_options: DjangoListConnection[MiraklInternalPropertyOptionType] = connection()

    mirakl_category: MiraklCategoryType = node()
    mirakl_categories: DjangoListConnection[MiraklCategoryType] = connection()

    mirakl_property: MiraklPropertyType = node()
    mirakl_properties: DjangoListConnection[MiraklPropertyType] = connection()

    mirakl_property_select_value: MiraklPropertySelectValueType = node()
    mirakl_property_select_values: DjangoListConnection[MiraklPropertySelectValueType] = connection()

    mirakl_property_applicability: MiraklPropertyApplicabilityType = node()
    mirakl_property_applicabilities: DjangoListConnection[MiraklPropertyApplicabilityType] = connection()

    mirakl_product_type_item: MiraklProductTypeItemType = node()
    mirakl_product_type_items: DjangoListConnection[MiraklProductTypeItemType] = connection()

    mirakl_product_category: MiraklProductCategoryType = node()
    mirakl_product_categories: DjangoListConnection[MiraklProductCategoryType] = connection()

    mirakl_product: MiraklProductType = node()
    mirakl_products: DjangoListConnection[MiraklProductType] = connection()

    mirakl_product_content: MiraklProductContentType = node()
    mirakl_product_contents: DjangoListConnection[MiraklProductContentType] = connection()

    mirakl_price: MiraklPriceType = node()
    mirakl_prices: DjangoListConnection[MiraklPriceType] = connection()

    mirakl_ean_code: MiraklEanCodeType = node()
    mirakl_ean_codes: DjangoListConnection[MiraklEanCodeType] = connection()

    mirakl_document_type: MiraklDocumentTypeType = node()
    mirakl_document_types: DjangoListConnection[MiraklDocumentTypeType] = connection()

    mirakl_import_process: MiraklSalesChannelImportType = node()
    mirakl_import_processes: DjangoListConnection[MiraklSalesChannelImportType] = connection()
