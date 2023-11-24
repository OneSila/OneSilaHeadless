from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from orders.models import Order, OrderItem, OrderNote
from .filters import OrderFilter, OrderItemFilter, OrderNoteFilter
from .ordering import OrderOrder, OrderItemOrder, OrderNoteOrder


@type(Order, filters=OrderFilter, order=OrderOrder, pagination=True, fields="__all__")
class OrderType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(OrderItem, filters=OrderItemFilter, order=OrderItemOrder, pagination=True, fields="__all__")
class OrderItemType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(OrderNote, filters=OrderNoteFilter, order=OrderNoteOrder, pagination=True, fields="__all__")
class OrderNoteType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
