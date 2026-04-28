from typing import Optional
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, lazy, ExcluideDemoDataFilterMixin

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter


@filter(SalesPrice)
class SalesPriceFilter(SearchFilterMixin):
    id: auto
    product: ProductFilter | None
    currency: CurrencyFilter | None


@filter(SalesPriceList)
class SalesPriceListFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    name: auto
    currency: Optional[CurrencyFilter]
    vat_included: auto
    auto_update_prices: auto
    auto_add_products: auto
    start_date: auto
    end_date: auto
    salespricelistitem: Optional[lazy['SalesPriceListItemFilter', "sales_prices.schema.types.filters"]]


@filter(SalesPriceListItem)
class SalesPriceListItemFilter(SearchFilterMixin):
    id: auto
    salespricelist: SalesPriceListFilter | None
    product: ProductFilter | None
