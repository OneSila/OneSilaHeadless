from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from inventory.models import Inventory, InventoryLocation


@input(Inventory, fields="__all__")
class InventoryInput:
    pass


@partial(Inventory, fields="__all__")
class InventoryPartialInput(NodeInput):
    pass


@input(InventoryLocation, fields="__all__")
class InventoryLocationInput:
    pass


@partial(InventoryLocation, fields="__all__")
class InventoryLocationPartialInput(NodeInput):
    pass
