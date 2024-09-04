from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field
from order_returns.models import OrderReturn, OrderReturnItem
from .types.types import OrderReturnType, OrderReturnItemType


@type(name='Query')
class OrderReturnsQuery:
    order_return: OrderReturnType = node()
    order_returns: ListConnectionWithTotalCount[OrderReturnType] = connection()

    order_return_item: OrderReturnItemType = node()
    order_return_items: ListConnectionWithTotalCount[OrderReturnItemType] = connection()
