from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from orders.models import Order, OrderItem, OrderNote
from orders.schema.types.types import OrderType, OrderItemType, OrderNoteType


@type(name="Subscription")
class OrdersSubscription:
    @subscription
    async def order(self, info: Info, pk: str) -> AsyncGenerator[OrderType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=Order):
            yield i

    @subscription
    async def order_item(self, info: Info, pk: str) -> AsyncGenerator[OrderItemType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=OrderItem):
            yield i

    @subscription
    async def order_note(self, info: Info, pk: str) -> AsyncGenerator[OrderNoteType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=OrderNote):
            yield i
