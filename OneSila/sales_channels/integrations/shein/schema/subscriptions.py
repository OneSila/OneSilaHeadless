"""GraphQL subscription mixins for the Shein integration."""

from typing import AsyncGenerator

from core.schema.core.subscriptions import Info, model_subscriber, subscription, type
from sales_channels.integrations.shein.models import SheinSalesChannel
from sales_channels.integrations.shein.schema.types.types import SheinSalesChannelType


@type(name="Subscription")
class SheinSalesChannelsSubscription:
    """Emit updates when Shein sales channels change."""

    @subscription
    async def shein_channel(
        self,
        info: Info,
        pk: str,
    ) -> AsyncGenerator[SheinSalesChannelType, None]:
        async for instance in model_subscriber(
            info=info,
            pk=pk,
            model=SheinSalesChannel,
        ):
            yield instance
