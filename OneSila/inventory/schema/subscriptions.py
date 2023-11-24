from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from inventory.models import Inventory, InventoryLocation
from inventory.schema.types.types import InventoryType, InventoryLocationType


@type(name="Subscription")
class InventorySubscription:
    @subscription
    async def inventory(self, info: Info, pk: str) -> AsyncGenerator[InventoryType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Inventory):
            yield i

    @subscription
    async def inventory_location(self, info: Info, pk: str) -> AsyncGenerator[InventoryLocationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=InventoryLocation):
            yield i
