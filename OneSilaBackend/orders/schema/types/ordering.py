from core.schema.types.ordering import order
from core.schema.types.types import auto

from orders.models import Order, OrderItem, OrderNote


@order(Order)
class OrderOrder:
    id: auto
    reference: auto
    status: auto


@order(OrderItem)
class OrderItemOrder:
    id: auto


@order(OrderNote)
class Order:
    id: auto
    order: auto
