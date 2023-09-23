from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from inventory.models import Inventory, InventoryLocation
from .filters import InventoryFilter, InventoryLocation
from .ordering import InventoryOrder, InventoryLocation


@type(Inventory, filters=InventoryFilter, order=InventoryOrder, pagination=True, fields="__all__")
class InventoryType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(InventoryLocation, filters=InventoryLocationFilter, order=InventoryLocationOrder, pagination=True, fields="__all__")
class InventoryLocationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
