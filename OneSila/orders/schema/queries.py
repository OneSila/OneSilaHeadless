from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import OrderType, OrderItemType, OrderNoteType


@type(name="Query")
class OrdersQuery:
    order: OrderType = node()
    orders: DjangoListConnection[OrderType] = connection()

    order_item: OrderItemType = node()
    order_items: DjangoListConnection[OrderItemType] = connection()

    order_note: OrderNoteType = node()
    order_notes: DjangoListConnection[OrderNoteType] = connection()
