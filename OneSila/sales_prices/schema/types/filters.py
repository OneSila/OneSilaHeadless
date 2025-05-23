from typing import Optional, Tuple
from contacts.schema.types.filters import CustomerFilter
from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, lazy, ExcluideDemoDataFilterMixin

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from products.schema.types.filters import ProductFilter
from currencies.schema.types.filters import CurrencyFilter
from django.db.models import Q, F, QuerySet
from strawberry_django import filter_field as custom_filter
from strawberry import UNSET


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
    customers: Optional[CustomerFilter]
    salespricelistitem: Optional[lazy['SalesPriceListItemFilter', "sales_prices.schema.types.filters"]]

    @custom_filter
    def currency_match_with_customers(
        self,
        queryset: QuerySet,
        value: Optional[bool],
        prefix: str
    ) -> Tuple[QuerySet, Q]:

        initial_queryset = queryset
        if value not in (None, UNSET):
            queryset = queryset.filter(customers__isnull=False)

            queryset = queryset.exclude(
                customers__currency=F('currency')
            ).distinct()

            if value:
                queryset = initial_queryset.exclude(id__in=queryset.values_list('id', flat=True))

        return queryset, Q()


@filter(SalesPriceListItem)
class SalesPriceListItemFilter(SearchFilterMixin):
    id: auto
    salespricelist: SalesPriceListFilter | None
    product: ProductFilter | None
