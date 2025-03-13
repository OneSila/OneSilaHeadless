from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.models import ImportProcess, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from .types.types import ImportProcessType, SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType
from ..integrations.magento2.models import MagentoSalesChannel
from ..integrations.magento2.schema.types.types import MagentoSalesChannelType


@type(name='Subscription')
class SalesChannelsSubscription:
    @subscription
    async def import_process(self, info: Info, pk: str) -> AsyncGenerator[ImportProcessType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ImportProcess):
            yield i

    @subscription
    async def sales_channel(self, info: Info, pk: str) -> AsyncGenerator[SalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesChannel):
            yield i

    @subscription
    async def sales_channel_integration_pricelist(self, info: Info, pk: str) -> AsyncGenerator[SalesChannelIntegrationPricelistType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesChannelIntegrationPricelist):
            yield i

    @subscription
    async def sales_channel_view(self, info: Info, pk: str) -> AsyncGenerator[SalesChannelViewType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesChannelView):
            yield i

    @subscription
    async def sales_channel_view_assign(self, info: Info, pk: str) -> AsyncGenerator[SalesChannelViewAssignType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesChannelViewAssign):
            yield i

    @subscription
    async def magento_channel(self, info: Info, pk: str) -> AsyncGenerator[MagentoSalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=MagentoSalesChannel):
            yield i