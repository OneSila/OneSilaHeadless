import strawberry
from asgiref.sync import sync_to_async
from strawberry.relay import from_base64

from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import InventoryType, InventoryLocationType, InventoryMovementType, PickingLocationType



@type(name="Query")
class InventoryQuery:
    inventory: InventoryType = node()
    inventories: ListConnectionWithTotalCount[InventoryType] = connection()

    inventory_location: InventoryLocationType = node()
    inventory_locations: ListConnectionWithTotalCount[InventoryLocationType] = connection()

    inventory_movement: InventoryMovementType = node()
    inventory_movements: ListConnectionWithTotalCount[InventoryMovementType] = connection()
