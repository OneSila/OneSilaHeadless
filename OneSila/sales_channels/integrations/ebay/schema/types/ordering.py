from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbayCategory,
    EbayProductCategory,
    EbayProductStoreCategory,
    EbaySalesChannel,
    EbayStoreCategory,
    EbayInternalProperty,
    EbayInternalPropertyOption,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelImport,
    EbaySalesChannelView,
    EbayCurrency,
    EbayDocumentType,
)


@order(EbaySalesChannel)
class EbaySalesChannelOrder:
    id: auto


@order(EbayCategory)
class EbayCategoryOrder:
    id: auto


@order(EbayProductCategory)
class EbayProductCategoryOrder:
    id: auto


@order(EbayStoreCategory)
class EbayStoreCategoryOrder:
    id: auto
    order: auto
    level: auto
    name: auto


@order(EbayProductStoreCategory)
class EbayProductStoreCategoryOrder:
    id: auto


@order(EbayProductType)
class EbayProductTypeOrder:
    id: auto


@order(EbayProductTypeItem)
class EbayProductTypeItemOrder:
    id: auto


@order(EbayProperty)
class EbayPropertyOrder:
    id: auto


@order(EbayInternalProperty)
class EbayInternalPropertyOrder:
    id: auto


@order(EbayInternalPropertyOption)
class EbayInternalPropertyOptionOrder:
    id: auto


@order(EbayPropertySelectValue)
class EbayPropertySelectValueOrder:
    id: auto


@order(EbaySalesChannelView)
class EbaySalesChannelViewOrder:
    id: auto


@order(EbaySalesChannelImport)
class EbaySalesChannelImportOrder:
    id: auto


@order(EbayCurrency)
class EbayCurrencyOrder:
    id: auto


@order(EbayDocumentType)
class EbayDocumentTypeOrder:
    id: auto
