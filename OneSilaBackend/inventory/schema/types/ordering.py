from core.schema.types.ordering import order
from core.schema.types.types import auto

from inventory.models import Inventory, InventoryLocation


@order(Inventory)
class InventoryOrder:
    id: auto
    location: auto


@order(InventoryLocation)
class InventoryLocationOrder:
    id: auto
    name: auto
    parent_location: auto
