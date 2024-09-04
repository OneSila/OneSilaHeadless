from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from order_returns.models import OrderReturn, OrderReturnItem


@order(OrderReturn)
class OrderReturnOrder:
    id: auto
    status: auto
    received_on: auto


@order(OrderReturnItem)
class OrderReturnItemOrder:
    id: auto
