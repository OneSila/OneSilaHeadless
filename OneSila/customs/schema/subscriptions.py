from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscribe_publisher

from customs.models import HsCode
from .types.types import HsCodeType


@type(name="Subscription")
class CustomsSubscription:
    @subscription
    async def hs_code(self, info: Info, pk: str) -> AsyncGenerator[HsCodeType, None]:
        async for i in model_subscribe_publisher(info=info, pk=pk, model=HsCode):
            yield i
