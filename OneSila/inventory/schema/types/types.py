from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List, Optional, Self

from inventory.models import Inventory, InventoryLocation
from products.schema.types.types import ProductType
from contacts.schema.types.types import InternalShippingAddressType
from .filters import InventoryFilter, InventoryLocationFilter
from .ordering import InventoryOrder, InventoryLocationOrder


@type(InventoryLocation, filters=InventoryLocationFilter, order=InventoryLocationOrder, pagination=True, fields="__all__")
class InventoryLocationType(relay.Node, GetQuerysetMultiTenantMixin):
    location: Optional[InternalShippingAddressType]


@type(Inventory, filters=InventoryFilter, order=InventoryOrder, pagination=True, fields="__all__")
class InventoryType(relay.Node, GetQuerysetMultiTenantMixin):
    product: ProductType
    stocklocation: InventoryLocationType
