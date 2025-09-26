from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.ebay.models import EbaySalesChannel, EbaySalesChannelImport
from sales_channels.integrations.ebay.schema.types.types import EbaySalesChannelType, EbaySalesChannelImportType


@type(name='Subscription')
class EbaySalesChannelsSubscription:
    @subscription
    async def ebay_channel(self, info: Info, pk: str) -> AsyncGenerator[EbaySalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=EbaySalesChannel):
            yield i

    @subscription
    async def ebay_import_process(self, info: Info, pk: str) -> AsyncGenerator[EbaySalesChannelImportType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=EbaySalesChannelImport):
            yield i
