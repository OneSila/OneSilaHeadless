from products.models import DropshipProduct, SupplierPrices
from purchasing.models import PurchaseOrder
from contacts.models import InternalCompany
from core.exceptions import SanityCheckError

import logging
logger = logging.getLogger(__name__)


class BuyDropShippingProductsFactory:
    def __init__(self, order):
        self.order = order
        self.orderitems = order.orderitem_set.all()
        self.multi_tenant_company = order.multi_tenant_company
        self.address_to = order.shipping_address
        self.purchaseorders_for_supplier = {}
        self.internal_contact = self.multi_tenant_company.multitenantuser_set.filter(is_multi_tenant_company_owner=True).first()

    def _sanity_check(self):
        if not self.internal_contact:
            raise SanityCheckError(f"Cannot create a purchase order without an internal contact")

    def get_reference(self, supplier):
        self.reference = f"POD-{supplier.id}-{self.order.reference}"

    def get_invoice_address(self):
        internal_company = InternalCompany.objects.get(multi_tenant_company=self.multi_tenant_company)
        return internal_company.address_set.get(is_invoice_address=True)

    def _set_dropshipping_orderitems(self):
        orderitem_product_ids = self.orderitems.values('product_id')
        dropshipproducts = DropshipProduct.objects.filter(id__in=orderitem_product_ids)
        self.dropshipping_orderitems = self.orderitems.filter(product_id__in=dropshipproducts.values('id')).distinct()

    def create_purchaseorders(self):
        for orderitem in self.dropshipping_orderitems.iterator():
            # We need to verify that we didn't already buy these products.
            # Therefor we will attach the purchaseorderitem to the orderitem.
            all_supplierproducts = orderitem.product.deflate_simple()
            # We can have multiple suppliers for a given purchased product.
            # For the qty needed, we'll just take the cheapest one.
            supplierprice = SupplierPrices.objects.find_cheapest(all_supplierproducts, orderitem.quantity)
            supplierproduct = supplierprice.supplier_product
            supplier = supplierproduct.supplier

            # Based on the info we gathered, build our purchase-orders.
            # keeping in mind that one SalesOrder can contain multiple
            # products coming from the same supplier.
            try:
                purchase_order = self.purchaseorders_for_supplier[supplier]
            except KeyError:
                purchase_order, _ = PurchaseOrder.objects.get_or_create(
                    multi_tenant_company=self.multi_tenant_company,
                    order_reference=self.get_reference(supplier),
                    order=self.order,
                    supplier=supplier,
                    currency=supplier.get_currency(),
                    invoice_address=self.get_invoice_address(),
                    shipping_address=self.address_to,
                    internal_contact=self.internal_contact)

                self.purchaseorders_for_supplier[supplier] = purchase_order
                logger.debug(f"Create PO {purchase_order}")

            po_item, _ = purchase_order.purchaseorderitem_set.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=supplierproduct,
                quantity=orderitem.quantity,
                unit_price=supplierprice.unit_price,
                orderitem=orderitem)
            logger.debug(f"Create {po_item=} for po {purchase_order} with product {orderitem.product}")

    def mark_purchaseorder_status(self):
        for po in self.purchaseorders_for_supplier.values():
            po.set_status_to_order()

    def run(self):
        self._sanity_check()
        self._set_dropshipping_orderitems()
        self.create_purchaseorders()
        self.mark_purchaseorder_status()
