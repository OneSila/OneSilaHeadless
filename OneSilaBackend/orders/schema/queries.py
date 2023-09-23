from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import OrderType, OrderItemType, OrderNoteType


@type(name="Query")
class OrderQuery:
    order: OrderType = node()
    orders: ListConnectionWithTotalCount[OrderType] = connection()

    order_item: OrderItemType = node()
    order_items: ListConnectionWithTotalCount[OrderItemType] = connection()

    order_note: OrderNoteTypeType = node()
    order_notes: ListConnectionWithTotalCount[OrderNoteTypeType] = connection()
