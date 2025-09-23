from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProductType,
    EbayProductTypeItem,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelImport,
    EbaySalesChannelView,
)


@order(EbaySalesChannel)
class EbaySalesChannelOrder:
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


@order(EbayPropertySelectValue)
class EbayPropertySelectValueOrder:
    id: auto


@order(EbaySalesChannelView)
class EbaySalesChannelViewOrder:
    id: auto


@order(EbaySalesChannelImport)
class EbaySalesChannelImportOrder:
    id: auto
