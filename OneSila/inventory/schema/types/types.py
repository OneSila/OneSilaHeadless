from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, auto
import strawberry
from typing import Optional

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from products.schema.types.types import ProductType
from contacts.schema.types.types import InventoryShippingAddressType
from .filters import InventoryFilter, InventoryLocationFilter, InventoryMovementFilter
from .ordering import InventoryOrder, InventoryLocationOrder


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


@type(InventoryMovement, pagination=True, filters=InventoryMovementFilter, fields="__all__")
class InventoryMovementType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType

    @field()
    def name(self, info) -> str:
        return self.name


@strawberry.type
class PickingLocationType:
    location: InventoryLocationType
    quantity: int
