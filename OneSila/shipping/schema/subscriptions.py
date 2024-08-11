from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from shipping.models import Shipment, Package, PackageItem
from .types.types import ShipmentType, PackageType, PackageItemType

import logging
logger = logging.getLogger(__name__)


@type(name="Subscription")
class ShippingSubscription:
    @subscription
    async def shipment(self, info: Info, pk: str) -> AsyncGenerator[ShipmentType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Shipment):
            yield i

    @subscription
    async def package(self, info: Info, pk: str) -> AsyncGenerator[PackageType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Package):
            yield i

    @subscription
    async def packageitem(self, info: Info, pk: str) -> AsyncGenerator[PackageItemType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=PackageItem):
            yield i
