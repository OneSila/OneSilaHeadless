from purchasing.factories import PurchaseOrderInventoryReceived


def purchaseorder_inventory_received(*, purchase_order, product, quantity):
    fac = PurchaseOrderInventoryReceived(purchase_order=purchase_order, product=product, quantity=quantity)
    fac.run()
