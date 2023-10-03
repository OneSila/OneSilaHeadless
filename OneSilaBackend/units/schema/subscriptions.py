from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from units.models import Unit
from units.schema.types.types import UnitType


@type(name="Subscription")
class UnitsSubscription:
    @subscription
    async def unit(self, info: Info, pk: str) -> AsyncGenerator[UnitType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=Unit):
            yield i
