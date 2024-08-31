from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from inventory.models import Inventory, InventoryLocation


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
