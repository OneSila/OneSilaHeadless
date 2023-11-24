from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import InventoryType, InventoryLocationType


@type(name="Query")
class InventoryQuery:
    pass
    inventory: InventoryType = node()
    inventories: ListConnectionWithTotalCount[InventoryType] = connection()

    inventory_location: InventoryLocationType = node()
    inventory_locations: ListConnectionWithTotalCount[InventoryLocationType] = connection()
