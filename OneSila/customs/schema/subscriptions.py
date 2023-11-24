from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from customs.models import HsCode
from .types.types import HsCodeType


@type(name="Subscription")
class CustomsSubscription:
    @subscription
    async def hs_code(self, info: Info, pk: str) -> AsyncGenerator[HsCodeType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=HsCode):
            yield i
