from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from taxes.models import Tax
from taxes.schema.types.types import TaxType


@type(name="Subscription")
class TaxSubscription:
    @subscription
    async def tax(self, info: Info, pk: str) -> AsyncGenerator[TaxType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=Tax):
            yield i
