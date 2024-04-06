from typing import List, Optional

from contacts.schema.types.filters import CustomerFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter


@filter(SalesPrice)
class SalesPriceFilter(SearchFilterMixin):
    search: str | None
    id: auto
    product: ProductFilter | None
    currency: CurrencyFilter | None

@filter(SalesPriceList)
class SalesPriceListFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    currency: Optional[CurrencyFilter]
    vat_included: auto
    auto_update: auto
    customers: Optional[CustomerFilter]
    salespricelistitem: Optional['SalesPriceListItemFilter']


@filter(SalesPriceListItem)
class SalesPriceListItemFilter(SearchFilterMixin):
    search: str | None
    id: auto
    salespricelist: SalesPriceListFilter | None
    product: ProductFilter | None
