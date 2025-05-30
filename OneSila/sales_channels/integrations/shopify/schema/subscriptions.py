from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.shopify.models import ShopifySalesChannel
from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType


@type(name='Subscription')
class ShopifySalesChannelsSubscription:

    @subscription
    async def shopify_channel(self, info: Info, pk: str) -> AsyncGenerator[ShopifySalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ShopifySalesChannel):
            yield i
