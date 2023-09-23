from core.schema.types.types import auto
from core.schema.types.filters import filter

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter


@filter(SalesPrice)
class SalesPriceFilter:
    id: auto
    product: ProductFilter
    currency: CurrencyFilter


@filter(SalesPriceList)
class SalesPriceListFilter:
    id: auto
    name: auto
    currency: CurrencyFilter
    vat_included: auto
    auto_update: auto


@filter(SalesPriceListItem)
class SalesPriceListItemFilter:
    id: auto
    salespricelist: SalesPriceListFilter
    product: ProductFilter
