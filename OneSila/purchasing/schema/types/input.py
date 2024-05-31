from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from purchasing.models import PurchaseOrder, PurchaseOrderItem


@input(PurchaseOrder, fields="__all__")
class PurchaseOrderInput:
    pass


@partial(PurchaseOrder, fields="__all__")
class PurchaseOrderPartialInput(NodeInput):
    pass


@input(PurchaseOrderItem, fields="__all__")
class PurchaseOrderItemInput:
    pass


@partial(PurchaseOrderItem, fields="__all__")
class PurchaseOrderItemPartialInput(NodeInput):
    pass
