from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonSalesChannelImport,
)
from sales_channels.integrations.amazon.schema.types.types import (
    AmazonSalesChannelType,
    AmazonPropertyType,
    AmazonPropertySelectValueType,
    AmazonSalesChannelImportType,
)


@type(name='Subscription')
class AmazonSalesChannelsSubscription:

    @subscription
    async def amazon_channel(self, info: Info, pk: str) -> AsyncGenerator[AmazonSalesChannelType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=AmazonSalesChannel):
            yield i

    @subscription
    async def amazon_property(self, info: Info, pk: str) -> AsyncGenerator[AmazonPropertyType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=AmazonProperty):
            yield i

    @subscription
    async def amazon_property_select_value(self, info: Info, pk: str) -> AsyncGenerator[AmazonPropertySelectValueType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=AmazonPropertySelectValue):
            yield i

    @subscription
    async def amazon_import_process(self, info: Info, pk: str) -> AsyncGenerator[AmazonSalesChannelImportType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=AmazonSalesChannelImport):
            yield i
