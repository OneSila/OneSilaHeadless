from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from purchasing.models import SupplierProduct, PurchaseOrder, \
    PurchaseOrderItem


@order(SupplierProduct)
class SupplierProductOrder:
    id: auto
    sku: auto
    name: auto


@order(PurchaseOrder)
class PurchaseOrderOrder:
    id: auto
    status: auto
    order_reference: auto


@order(PurchaseOrderItem)
class PurchaseOrderItemOrder:
    id: auto
