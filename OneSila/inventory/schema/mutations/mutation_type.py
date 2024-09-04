from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from ..types.types import InventoryType, InventoryLocationType, InventoryMovementType
from ..types.input import InventoryInput, InventoryLocationInput, \
    InventoryPartialInput, InventoryLocationPartialInput, InventoryMovementInput, \
    InventoryMovementPartialInput
from .fields import update_inventory_movement, create_inventory_movement


@type(name="Mutation")
class InventoryMutation:
    create_inventory: InventoryType = create(InventoryInput)
    create_inventories: List[InventoryType] = create(InventoryInput)
    update_inventory: InventoryType = update(InventoryPartialInput)
    delete_inventory: InventoryType = delete()
    delete_inventories: List[InventoryType] = delete()

    create_inventory_location: InventoryLocationType = create(InventoryLocationInput)
    create_inventory_locations: List[InventoryLocationType] = create(InventoryLocationInput)
    update_inventory_location: InventoryLocationType = update(InventoryLocationPartialInput)
    delete_inventory_location: InventoryLocationType = delete()
    delete_inventory_locations: List[InventoryLocationType] = delete()

    create_inventory_movement: InventoryMovementType = create_inventory_movement()
    create_inventory_movements: List[InventoryMovementType] = create(InventoryMovementInput)
    update_inventory_movement: InventoryMovementType = update_inventory_movement()
    delete_inventory_movement: InventoryMovementType = delete()
    delete_inventory_movements: List[InventoryMovementType] = delete()
