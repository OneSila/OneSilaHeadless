from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field

from typing import List, Optional

from currencies.schema.types.types import CurrencyType
from products.schema.types.types import ProductType
from sales_prices.models import SalesPrice, SalesPriceList, \
    SalesPriceListItem
from .filters import SalesPriceFilter, SalesPriceListFilter, \
    SalesPriceListItemFilter
from .ordering import SalesPriceOrder, SalesPriceListOrder, \
    SalesPriceListItemOrder


@type(SalesPrice, filters=SalesPriceFilter, order=SalesPriceOrder, pagination=True, fields="__all__")
class SalesPriceType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType
    currency: Optional[CurrencyType]

    @field
    def real_id(self) -> float | None:
        return self.id

@type(SalesPriceList, filters=SalesPriceListFilter, order=SalesPriceListOrder, pagination=True, fields="__all__")
class SalesPriceListType(relay.Node, GetQuerysetMultiTenantMixin):
    currency: CurrencyType
    customers: List[CompanyType]
    salespricelistitem_set: List['SalesPriceListItemType']


@type(SalesPriceListItem, filters=SalesPriceListItemFilter, order=SalesPriceListItemOrder, pagination=True, fields="__all__")
class SalesPriceListItemType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType
    salespricelist: SalesPriceListType

    @field
    def price(self) -> float | None:
        return self.price

    @field
    def discount(self) -> float | None:
        return self.discount
