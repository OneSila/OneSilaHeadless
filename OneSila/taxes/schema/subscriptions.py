from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from taxes.models import Tax
from taxes.schema.types.types import TaxType


@type(name="Subscription")
class TaxSubscription:
    @subscription
    async def tax(self, info: Info, pk: str) -> AsyncGenerator[TaxType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Tax):
            yield i
