from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from lead_times.models import LeadTime, LeadTimeForShippingAddress
from lead_times.schema.types.types import LeadTimeType, LeadTimeForShippingAddressType


@type(name="Subscription")
class LeadTimesSubscription:
    @subscription
    async def lead_time(self, info: Info, pk: str) -> AsyncGenerator[LeadTimeType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=LeadTime):
            yield i

    @subscription
    async def lead_time_for_shippingaddress(self, info: Info, pk: str) -> AsyncGenerator[LeadTimeForShippingAddressType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=LeadTimeForShippingAddress):
            yield i