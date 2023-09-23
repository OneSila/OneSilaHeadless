from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from orders.models import Order, OrderItem, OrderNote


@input(Order, fields="__all__")
class OrderInput:
    pass


@partial(Order, fields="__all__")
class OrderPartialInput(NodeInput):
    pass


@input(OrderItem, fields="__all__")
class OrderItemInput:
    pass


@partial(OrderItem, fields="__all__")
class OrderItemPartialInput(NodeInput):
    pass


@input(OrderNote, fields="__all__")
class OrderNoteInput:
    pass


@partial(OrderNote, fields="__all__")
class OrderNotePartialInput(NodeInput):
    pass
