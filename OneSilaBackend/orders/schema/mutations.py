from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import OrderType, OrderItemType, OrderNoteType
from .types.input import OrderInput, OrderItemInput, OrderNoteInput\
    OrderPartialInput, OrderItemPartialInput, OrderNotePartialInput


@type(name="Mutation")
class Mutation:
    create_order: OrderType = create(OrderInput)
    create_orders: List[OrderType] = create(OrderInput)
    update_order: OrderType = update(OrderPartialInput)

    create_order_item: OrderItemType = create(OrderItemInput)
    create_order_items: List[OrderItemType] = create(OrderItemInput)
    update_order_item: OrderItemType = update(OrderItemPartialInput)
    delete_order_item: OrderItemType = delete()
    delete_order_items: List[OrderItemType] = delete()

    create_order_note: OrderNoteType = create(OrderNoteInput)
    create_order_notes: List[OrderNoteType] = create(OrderNoteInput)
    update_order_note: OrderNoteType = update(OrderNotePartialInput)
    delete_order_note: OrderNoteType = delete()
    delete_order_notes: List[OrderNoteType] = delete()
