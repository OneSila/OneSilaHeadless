from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from inventory.models import Inventory, InventoryLocation, InventoryMovement
from inventory.schema.types.types import InventoryType
from purchasing.schema.types.types import PurchaseOrderType
from shipments.schema.types.types import PackageType

# Quantity is disabled as we never set quantity directly.
# You must add an InventoryMovement from or to this Inventory.


@input(Inventory, exclude=['quantity'])
class InventoryInput:
    pass

# Quantity is disabled as we never set quantity directly.
# You must add an InventoryMovement from or to this Inventory.


@partial(Inventory, exclude=['quantity'])
class InventoryPartialInput(NodeInput):
    pass


@input(InventoryLocation, fields="__all__")
class InventoryLocationInput:
    pass


@partial(InventoryLocation, fields="__all__")
class InventoryLocationPartialInput(NodeInput):
    pass


# @input(InventoryMovement, fields="__all__")
# class InventoryMovementInput:
#     pass

# @partial(InventoryMovement, fields="__all__")
# class InventoryMovementPartialInput(NodeInput):
#     pass

@input(InventoryMovement)
class InventoryMovementInput:
    movement_from: PurchaseOrderType | InventoryType
    movement_to: PackageType | InventoryType
    product: auto
    quantity: auto
    notes: auto


@partial(InventoryMovement)
class InventoryMovementPartialInput(NodeInput):
    movement_from: PurchaseOrderType | InventoryType
    movement_to: PackageType | InventoryType
    product: auto
    quantity: auto
    notes: auto
