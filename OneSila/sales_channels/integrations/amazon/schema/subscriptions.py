from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.schema.types.types import AmazonSalesChannelType


@type(name='Subscription')
class AmazonSalesChannelsSubscription:

    @subscription
    async def amazon_channel(self, info: Info, pk: str) -> AsyncGenerator[AmazonSalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=AmazonSalesChannel):
            yield i
