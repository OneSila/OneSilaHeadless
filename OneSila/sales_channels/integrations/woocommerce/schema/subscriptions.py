from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.integrations.woocommerce.schema.types.types import WoocommerceSalesChannelType


@type(name='Subscription')
class WoocommerceSalesChannelsSubscription:

    @subscription
    async def woocommerce_channel(self, info: Info, pk: str) -> AsyncGenerator[WoocommerceSalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=WoocommerceSalesChannel):
            yield i
