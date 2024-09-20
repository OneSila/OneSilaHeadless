from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.models import ImportCurrency, ImportImage, ImportProcess, ImportProduct, ImportProperty, ImportPropertySelectValue, ImportVat, RemoteCategory, RemoteCurrency, RemoteCustomer, RemoteImage, RemoteImageProductAssociation, RemoteInventory, RemoteLog, RemoteOrder, RemotePrice, RemoteProduct, RemoteProductContent, RemoteProductProperty, RemoteProperty, RemotePropertySelectValue, RemoteTaskQueue, RemoteVat, SalesChannel, SalesChannelIntegrationPricelist, SalesChannelView, SalesChannelViewAssign
from .types.types import ImportCurrencyType, ImportImageType, ImportProcessType, ImportProductType, ImportPropertyType, ImportPropertySelectValueType, ImportVatType, RemoteCategoryType, RemoteCurrencyType, RemoteCustomerType, RemoteImageType, RemoteImageProductAssociationType, RemoteInventoryType, RemoteLogType, RemoteOrderType, RemotePriceType, RemoteProductType, RemoteProductContentType, RemoteProductPropertyType, RemotePropertyType, RemotePropertySelectValueType, RemoteTaskQueueType, RemoteVatType, SalesChannelType, SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType


@type(name='Subscription')
class SalesChannelsSubscription:
    @subscription
    async def import_process(self, info: Info, pk: str) -> AsyncGenerator[ImportProcessType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ImportProcess):
            yield i

    @subscription
    async def remote_task_queue(self, info: Info, pk: str) -> AsyncGenerator[RemoteTaskQueueType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=RemoteTaskQueue):
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
