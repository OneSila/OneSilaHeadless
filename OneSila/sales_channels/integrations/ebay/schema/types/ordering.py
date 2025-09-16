from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbayInternalProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbaySalesChannelView,
)


@order(EbaySalesChannel)
class EbaySalesChannelOrder:
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
