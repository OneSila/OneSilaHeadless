from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.ebay.models import EbaySalesChannel
from sales_channels.integrations.ebay.schema.types.types import EbaySalesChannelType


@type(name='Subscription')
class EbaySalesChannelsSubscription:
    @subscription
    async def ebay_channel(self, info: Info, pk: str) -> AsyncGenerator[EbaySalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=EbaySalesChannel):
            yield i
