from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, auto
from core.models import Model

from typing import List, Optional, Self

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from products.schema.types.types import ProductType
from contacts.schema.types.types import InventoryShippingAddressType
from .filters import InventoryFilter, InventoryLocationFilter
from .ordering import InventoryOrder, InventoryLocationOrder
from purchasing.schema.types.types import PurchaseOrderType
from shipments.schema.types.types import PackageType
from order_returns.schema.types.types import OrderReturnType


@type(InventoryLocation, filters=InventoryLocationFilter, order=InventoryLocationOrder, pagination=True, fields="__all__")
class InventoryLocationType(relay.Node, GetQuerysetMultiTenantMixin):
    shippingaddress: Optional[InventoryShippingAddressType]

    @field()
    def is_internal_location(self, info) -> bool:
        return self.shippingaddress.company.is_internal_company


@type(Inventory, filters=InventoryFilter, order=InventoryOrder, pagination=True, fields="__all__")
class InventoryType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType
    inventorylocation: InventoryLocationType


@type(InventoryMovement, pagination=True, fields="__all__")
class InventoryMovementType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType

    @field()
    def movement_to(self, info) -> PackageType | InventoryType:
        return self.movement_to

    @field()
    def movement_from(self, info) -> PurchaseOrderType | InventoryType | OrderReturnType:
        return self.movement_from
