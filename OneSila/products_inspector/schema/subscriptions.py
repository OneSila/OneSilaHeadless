from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from products_inspector.models import Inspector
from products_inspector.schema.types.types import InspectorType


@type(name="Subscription")
class ProductsInspectorSubscription:
    @subscription
    async def inspector(self, info: Info, pk: str) -> AsyncGenerator[InspectorType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Inspector):
            yield i
