from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from eancodes.models import EanCode
from eancodes.schema.types.types import EanCodeType


@type(name="Subscription")
class EanCodesSubscription:
    @subscription
    async def ean_code(self, info: Info, pk: str) -> AsyncGenerator[EanCodeType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=EanCode):
            yield i
