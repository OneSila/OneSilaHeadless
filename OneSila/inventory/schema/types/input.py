from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial
from strawberry.relay import GlobalID

from inventory.models import Inventory, InventoryLocation, InventoryMovement


INVENTORY_MOVEMENT_EXCLUDES = ['mf_content_type', 'mf_object_id', 'mt_content_type', 'mt_object_id', 'movement_from', 'movement_to']


@input(Inventory, exclude=['quantity'])
class InventoryInput:
    # Quantity is disabled as we never set quantity directly.
    # You must add an InventoryMovement from or to this Inventory.
    pass


@partial(Inventory, exclude=['quantity'])
class InventoryPartialInput(NodeInput):
    # Quantity is disabled as we never set quantity directly.
    # You must add an InventoryMovement from or to this Inventory.
    pass


@input(InventoryLocation, fields="__all__")
class InventoryLocationInput:
    pass


@partial(InventoryLocation, fields="__all__")
class InventoryLocationPartialInput(NodeInput):
    pass


@input(InventoryMovement, exclude=INVENTORY_MOVEMENT_EXCLUDES)
class InventoryMovementInput:
    movement_from_id: GlobalID
    movement_to_id: GlobalID


@partial(InventoryMovement, exclude=INVENTORY_MOVEMENT_EXCLUDES)
class InventoryMovementPartialInput(NodeInput):
    movement_from_id: GlobalID
    movement_to_id: GlobalID
