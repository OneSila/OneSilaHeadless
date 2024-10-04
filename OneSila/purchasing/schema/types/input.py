from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial
from purchasing.models import PurchaseOrder, PurchaseOrderItem


@input(PurchaseOrder, fields="__all__")
class PurchaseOrderInput:
    pass


@partial(PurchaseOrder, fields="__all__")
class PurchaseOrderPartialInput(NodeInput):
    pass


# We cannot set quantity_recieved directly.  You
# MUST use an InventoryMovement from the PurchaseOrder to an Inventory
@input(PurchaseOrderItem, exclude=["quantity_recieved"])
class PurchaseOrderItemInput:
    pass

# We cannot set quantity_recieved directly.  You
# MUST use an InventoryMovement from the PurchaseOrder to an Inventory
@partial(PurchaseOrderItem, exclude=["quantity_recieved"])
class PurchaseOrderItemPartialInput(NodeInput):
    pass
