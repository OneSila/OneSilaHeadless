from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List

from order_returns.models import OrderReturn, OrderReturnItem


@input(OrderReturn, fields="__all__")
class OrderReturnInput:
    pass


@partial(OrderReturn, fields="__all__")
class OrderReturnPartialInput(NodeInput):
    pass


@input(OrderReturnItem, fields="__all__")
class OrderReturnItemInput:
    pass


@partial(OrderReturnItem, fields="__all__")
class OrderReturnItemPartialInput(NodeInput):
    pass
