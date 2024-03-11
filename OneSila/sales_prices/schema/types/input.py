from contacts.schema.types.input import CustomerPartialInput
from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial
from typing import List
from sales_prices.models import SalesPrice, SalesPriceList, \
    SalesPriceListItem


@input(SalesPrice, fields="__all__")
class SalesPriceInput:
    pass


@partial(SalesPrice, fields="__all__")
class SalesPricePartialInput(NodeInput):
    pass


@input(SalesPriceList, fields="__all__")
class SalesPriceListInput:
    customers: List[CustomerPartialInput]


@partial(SalesPriceList, fields="__all__")
class SalesPriceListPartialInput(NodeInput):
    customers: List[CustomerPartialInput] | None


@input(SalesPriceListItem, fields="__all__")
class SalesPriceListItemInput:
    pass


@partial(SalesPriceListItem, fields="__all__")
class SalesPriceListItemPartialInput(NodeInput):
    pass
