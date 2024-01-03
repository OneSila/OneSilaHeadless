from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter


@filter(SalesPrice)
class SalesPriceFilter(SearchFilterMixin):
    search: str | None
    id: auto
    product: ProductFilter
    currency: CurrencyFilter


@filter(SalesPriceList)
class SalesPriceListFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    currency: CurrencyFilter
    vat_included: auto
    auto_update: auto


@filter(SalesPriceListItem)
class SalesPriceListItemFilter(SearchFilterMixin):
    search: str | None
    id: auto
    salespricelist: SalesPriceListFilter
    product: ProductFilter
