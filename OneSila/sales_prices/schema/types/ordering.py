from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from currencies.schema.types.ordering import CurrencyOrder

from sales_prices.models import SalesPrice, SalesPriceList, \
    SalesPriceListItem


@order(SalesPrice)
class SalesPriceOrder:
    id: auto
    currency: CurrencyOrder | None


@order(SalesPriceList)
class SalesPriceListOrder:
    id: auto
    name: auto
    vat_included: auto
    auto_update_prices: auto
    auto_add_products: auto


@order(SalesPriceListItem)
class SalesPriceListItemOrder:
    id: auto
