from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from purchasing.models import PurchaseOrder, PurchaseOrderItem


@order(PurchaseOrder)
class PurchaseOrderOrder:
    id: auto
    status: auto
    order_reference: auto
    created_at: auto


@order(PurchaseOrderItem)
class PurchaseOrderItemOrder:
    id: auto
