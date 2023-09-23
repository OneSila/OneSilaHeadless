from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from sales_prices.models import SalesPrice, SalesPriceList\
    SalesPriceListItem
from .filters import SalesPriceFilter, SalesPriceListFilter, SalesPriceListItemFilter
from .ordering import SalesPriceOrder, SalesPriceListOrder, SalesPriceListItemOrder


@type(SalesPrice, filters=SalesPriceFilter, order=SalesPriceOrder, pagination=True, fields="__all__")
class SalesPriceType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(SalesPriceList, filters=SalesPriceListFilter, order=SalesPriceListOrder, pagination=True, fields="__all__")
class SalesPriceListType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(SalesPriceListItem, filters=SalesPriceListItemFilter, order=SalesPriceListItemOrder, pagination=True, fields="__all__")
class SalesPriceListItemType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
