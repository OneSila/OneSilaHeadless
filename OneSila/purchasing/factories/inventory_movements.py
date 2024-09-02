
class PurchaseOrderInventoryReceived:
    def __init__(self, *, purchase_order, product, quantity):
        self.purchase_order = purchase_order
        self.product = product
        self.quantity = quantity
        self.multi_tenant_company = purchase_order.multi_tenant_company

    def _set_purchaseorder_item(self):
        # Why get or create?  If we recieve good we didn't oder, we want to see that.
        self.purchaseorder_item, _ = self.purchase_order.purchaseorderitem_set.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product)

    def _populate_quantity_received(self):
        self.purchaseorder_item.add_quantity_received(self.quantity)

    def run(self):
        self._set_purchaseorder_item()
        self._populate_quantity_received()
