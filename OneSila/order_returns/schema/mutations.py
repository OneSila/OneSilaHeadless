from core.schema.core.mutations import create, update, delete, type, List, field
from .types.types import OrderReturnType, OrderReturnItemType
from .types.input import OrderReturnInput, OrderReturnPartialInput, OrderReturnItemInput, OrderReturnItemPartialInput


@type(name='Mutation')
class OrderReturnsMutation:
    create_order_return: OrderReturnType = create(OrderReturnInput)
    create_order_returns: List[OrderReturnType] = create(OrderReturnInput)
    update_order_return: OrderReturnType = update(OrderReturnPartialInput)
    delete_order_return: OrderReturnType = delete()
    delete_order_returns: List[OrderReturnType] = delete()

    create_order_return_item: OrderReturnItemType = create(OrderReturnItemInput)
    create_order_return_items: List[OrderReturnItemType] = create(OrderReturnItemInput)
    update_order_return_item: OrderReturnItemType = update(OrderReturnItemPartialInput)
    delete_order_return_item: OrderReturnItemType = delete()
    delete_order_return_items: List[OrderReturnItemType] = delete()
