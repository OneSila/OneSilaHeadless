from core.schema.types.ordering import order
from core.schema.types.types import auto

from sales_prices.models import SalesPrice, SalesPriceList\
    SalesPriceListItem


@order(SalesPrice)
class SalesPriceOrder:
    id: auto


@order(SalesPriceList)
class SalesPriceListOrder:
    id: auto
    name: auto
    vat_included: auto
    auto_update: auto


@order(SalesPriceListItem)
class SalesPriceListItemOrder:
    pass
