from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from eancodes.models import EanCode
from eancodes.schema.types.types import EanCodeType


@type(name="Subscription")
class EanCodesSubscription:
    @subscription
    async def ean_code(self, info: Info, pk: str) -> AsyncGenerator[EanCodeType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=EanCode):
            yield i
