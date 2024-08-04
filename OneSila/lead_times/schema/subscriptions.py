from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from lead_times.models import LeadTime, LeadTimeForShippingAddress, \
    LeadTimeProductOutOfStock
from lead_times.schema.types.types import LeadTimeType, LeadTimeForShippingAddressType, \
    LeadTimeProductOutOfStockType


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

    @subscription
    async def lead_time_product_out_of_stock(self, info: Info, pk: str) -> AsyncGenerator[LeadTimeProductOutOfStockType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=LeadTimeProductOutOfStock):
            yield i
