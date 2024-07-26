from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from lead_times.models import LeadTime, LeadTimeTranslation
from lead_times.schema.types.types import LeadTimeType, LeadTimeTranslationType


@type(name="Subscription")
class LeadTimesSubscription:
    @subscription
    async def lead_time(self, info: Info, pk: str) -> AsyncGenerator[LeadTimeType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=LeadTime):
            yield i

    @subscription
    async def lead_time_translation(self, info: Info, pk: str) -> AsyncGenerator[LeadTimeTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=LeadTimeTranslation):
            yield i
