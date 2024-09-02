from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from inventory.schema.types.types import InventoryType, InventoryLocationType, InventoryMovementType


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

    @subscription
    async def inventory_movement(self, info: Info, pk: str) -> AsyncGenerator[InventoryMovementType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=InventoryMovement):
            yield i
