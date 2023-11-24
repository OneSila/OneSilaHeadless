from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import OrderType, OrderItemType, OrderNoteType


@type(name="Query")
class OrdersQuery:
    order: OrderType = node()
    orders: ListConnectionWithTotalCount[OrderType] = connection()

    order_item: OrderItemType = node()
    order_items: ListConnectionWithTotalCount[OrderItemType] = connection()

    order_note: OrderNoteType = node()
    order_notes: ListConnectionWithTotalCount[OrderNoteType] = connection()
