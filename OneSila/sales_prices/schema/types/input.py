from contacts.schema.types.input import CustomerPartialInput
from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial
from typing import List, Optional
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
    customers: Optional[List[CustomerPartialInput]]


@partial(SalesPriceList, fields="__all__")
class SalesPriceListPartialInput(NodeInput):
    customers: Optional[List[CustomerPartialInput]]


@input(SalesPriceListItem, fields="__all__")
class SalesPriceListItemInput:
    pass


@partial(SalesPriceListItem, fields="__all__")
class SalesPriceListItemPartialInput(NodeInput):
    pass
