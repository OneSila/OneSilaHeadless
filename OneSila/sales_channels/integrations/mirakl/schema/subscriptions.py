from core.schema.core.subscriptions import AsyncGenerator, Info, model_subscriber, subscription, type
from sales_channels.integrations.mirakl.models import MiraklSalesChannel, MiraklSalesChannelImport
from sales_channels.integrations.mirakl.schema.types.types import (
    MiraklSalesChannelImportType,
    MiraklSalesChannelType,
)


@type(name="Subscription")
class MiraklSalesChannelsSubscription:
    @subscription
    async def mirakl_channel(self, info: Info, pk: str) -> AsyncGenerator[MiraklSalesChannelType, None]:
        async for item in model_subscriber(info=info, pk=pk, model=MiraklSalesChannel):
            yield item

    @subscription
    async def mirakl_import_process(self, info: Info, pk: str) -> AsyncGenerator[MiraklSalesChannelImportType, None]:
        async for item in model_subscriber(info=info, pk=pk, model=MiraklSalesChannelImport):
            yield item
