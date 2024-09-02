from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from order_returns.models import OrderReturn, OrderReturnItem
from .types.types import OrderReturnType, OrderReturnItemType


@type(name='Subscription')
class OrderReturnsSubscription:
    @subscription
    async def order_return(self, info: Info, pk: str) -> AsyncGenerator[OrderReturnType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=OrderReturn):
            yield i

    @subscription
    async def order_return_item(self, info: Info, pk: str) -> AsyncGenerator[OrderReturnItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=OrderReturnItem):
            yield i
