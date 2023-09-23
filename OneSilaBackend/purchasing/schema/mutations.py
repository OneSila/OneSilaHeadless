from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import SupplierProductType, PurchaseOrderType, \
    PurchaseOrderItemType
from .types.input import SupplierProductInput, PurchaseOrderInput, \
    PurchaseOrderItemInput, SupplierProductPartialInput, \
    PurchaseOrderPartialInput, PurchaseOrderItemPartialInput


@type(name="Mutation")
class Mutation:
    create_supplier_product: SupplierProductType = create(SupplierProductInput)
    create_supplier_products: List[SupplierProductType] = create(SupplierProductInput)
    update_supplier_product: SupplierProductType = update(SupplierProductPartialInput)
    delete_supplier_product: SupplierProductType = delete()
    delete_supplier_products: List[SupplierProductType] = delete()

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
