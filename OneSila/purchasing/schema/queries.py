from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import SupplierProductType, PurchaseOrderType, \
    PurchaseOrderItemType


@type(name="Query")
class PurchasingQuery:
    supplier_product: SupplierProductType = node()
    supplier_products: ListConnectionWithTotalCount[SupplierProductType] = connection()

    purchase_order: PurchaseOrderType = node()
    purchase_orders: ListConnectionWithTotalCount[PurchaseOrderType] = connection()

    purchase_order_item: PurchaseOrderItemType = node()
    purchase_order_items: ListConnectionWithTotalCount[PurchaseOrderItemType] = connection()
