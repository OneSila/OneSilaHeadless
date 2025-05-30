from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import InventoryType, InventoryLocationType, InventoryMovementType


@type(name="Query")
class InventoryQuery:
    inventory: InventoryType = node()
    inventories: DjangoListConnection[InventoryType] = connection()

    inventory_location: InventoryLocationType = node()
    inventory_locations: DjangoListConnection[InventoryLocationType] = connection()

    inventory_movement: InventoryMovementType = node()
    inventory_movements: DjangoListConnection[InventoryMovementType] = connection()
