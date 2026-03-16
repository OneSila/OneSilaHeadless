from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklDocumentType,
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductIssue,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklRemoteCurrency,
    MiraklRemoteLanguage,
    MiraklSalesChannel,
    MiraklSalesChannelImport,
    MiraklSalesChannelView,
)


@order(MiraklSalesChannel)
class MiraklSalesChannelOrder:
    id: auto


@order(MiraklSalesChannelView)
class MiraklSalesChannelViewOrder:
    id: auto


@order(MiraklRemoteCurrency)
class MiraklRemoteCurrencyOrder:
    id: auto


@order(MiraklRemoteLanguage)
class MiraklRemoteLanguageOrder:
    id: auto


@order(MiraklCategory)
class MiraklCategoryOrder:
    id: auto
    name: auto
    level: auto


@order(MiraklDocumentType)
class MiraklDocumentTypeOrder:
    id: auto
    name: auto


@order(MiraklProductType)
class MiraklProductTypeOrder:
    id: auto
    name: auto


@order(MiraklProperty)
class MiraklPropertyOrder:
    id: auto


@order(MiraklPropertySelectValue)
class MiraklPropertySelectValueOrder:
    id: auto


@order(MiraklProductTypeItem)
class MiraklProductTypeItemOrder:
    id: auto


@order(MiraklProductCategory)
class MiraklProductCategoryOrder:
    id: auto


@order(MiraklProduct)
class MiraklProductOrder:
    id: auto


@order(MiraklProductIssue)
class MiraklProductIssueOrder:
    id: auto
    main_code: auto
    code: auto
    severity: auto
    is_rejected: auto


@order(MiraklProductContent)
class MiraklProductContentOrder:
    id: auto


@order(MiraklPrice)
class MiraklPriceOrder:
    id: auto


@order(MiraklEanCode)
class MiraklEanCodeOrder:
    id: auto


@order(MiraklSalesChannelImport)
class MiraklSalesChannelImportOrder:
    id: auto
    created_at: auto
