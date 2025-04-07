from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.magento2.models import MagentoSalesChannel
from sales_channels.integrations.magento2.schema.types.types import MagentoSalesChannelType


@type(name='Subscription')
class MagentoSalesChannelsSubscription:

    @subscription
    async def magento_channel(self, info: Info, pk: str) -> AsyncGenerator[MagentoSalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=MagentoSalesChannel):
            yield i
