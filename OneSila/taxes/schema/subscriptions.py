from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from taxes.models import VatRate
from taxes.schema.types.types import VatRateType


@type(name="Subscription")
class TaxSubscription:
    @subscription
    async def tax(self, info: Info, pk: str) -> AsyncGenerator[VatRateType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=VatRate):
            yield i
