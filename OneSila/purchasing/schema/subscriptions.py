from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from purchasing.models import PurchaseOrder, PurchaseOrderItem
from purchasing.schema.types.types import SupplierProductType, PurchaseOrderType, \
    PurchaseOrderItemType


@type(name="Subscription")
class PurchasingSubscription:
    @subscription
    async def purchase_order(self, info: Info, pk: str) -> AsyncGenerator[PurchaseOrderType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PurchaseOrder):
            yield i

    @subscription
    async def purchase_order_item(self, info: Info, pk: str) -> AsyncGenerator[PurchaseOrderItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PurchaseOrderItem):
            yield i
