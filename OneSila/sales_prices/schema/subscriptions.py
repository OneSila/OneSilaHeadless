from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from sales_prices.schema.types.types import SalesPriceType, SalesPriceListType, \
    SalesPriceListItemType


@type(name="Subscription")
class SalesPriceSubscription:
    @subscription
    async def sales_price(self, info: Info, pk: str) -> AsyncGenerator[SalesPriceType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesPrice):
            yield i

    @subscription
    async def sales_price_list(self, info: Info, pk: str) -> AsyncGenerator[SalesPriceListItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesPriceList):
            yield i

    @subscription
    async def sales_price_list_item(self, info: Info, pk: str) -> AsyncGenerator[SalesPriceListItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SalesPriceListItem):
            yield i
