from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import PurchaseOrderType, PurchaseOrderItemType
from .types.input import PurchaseOrderInput, PurchaseOrderItemInput, PurchaseOrderPartialInput, PurchaseOrderItemPartialInput


@type(name="Mutation")
class PurchasingMutation:
    create_purchase_order: PurchaseOrderType = create(PurchaseOrderInput)
    create_purchase_orders: List[PurchaseOrderType] = create(PurchaseOrderInput)
    update_purchase_order: PurchaseOrderType = update(PurchaseOrderPartialInput)
    delete_purchase_order: PurchaseOrderType = delete()
    delete_purchase_orders: List[PurchaseOrderType] = delete()

    create_purchase_order_item: PurchaseOrderItemType = create(PurchaseOrderItemInput)
    create_purchase_order_items: List[PurchaseOrderItemType] = create(PurchaseOrderItemInput)
    update_purchase_order_item: PurchaseOrderItemType = update(PurchaseOrderItemPartialInput)
    delete_purchase_order_item: PurchaseOrderItemType = delete()
    delete_purchase_order_items: List[PurchaseOrderItemType] = delete()
