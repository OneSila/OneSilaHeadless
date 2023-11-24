from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from inventory.models import Inventory, InventoryLocation


@order(Inventory)
class InventoryOrder:
    id: auto


@order(InventoryLocation)
class InventoryLocationOrder:
    id: auto
