from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import InventoryType, InventoryLocationType
from .types.input import InventoryInput, InventoryLocationInput, \
    InventoryPartialInput, InventoryLocationPartialInput


@type(name="Mutation")
class Mutation:
    create_inventory: InventoryType = create(InventoryInput)
    create_inventories: List[InventoryType] = create(InventoryInput)
    update_inventory: InventoryType = update(InventoryLocationInput)
    delete_inventory: InventoryType = delete()
    delete_inventories: List[InventoryType] = delete()

    create_inventory_location_type: InventoryLocationType = create(InventoryLocationInput)
    create_inventory_location_types: List[InventoryLocationType] = create(InventoryLocationInput)
    update_inventory_location_type: InventoryLocationType = update(InventoryLocationPartialInput)
    delete_inventory_location_type: InventoryLocationType = delete()
    delete_inventory_location_types: List[InventoryLocationType] = delete()
