from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from purchasing.models import SupplierProduct, PurchaseOrder, \
    PurchaseOrderItem


@input(SupplierProduct, fields="__all__")
class SupplierProductInput:
    pass


@partial(SupplierProduct, fields="__all__")
class SupplierProductPartialInput(NodeInput):
    pass


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
