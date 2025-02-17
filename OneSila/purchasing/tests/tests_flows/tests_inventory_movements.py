from core.tests import TestCase, TestCaseDemoDataMixin
from products.demo_data import SUPPLIER_WOODEN_CHAIR_SKU
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from purchasing.flows import purchaseorder_inventory_received
from purchasing.models import PurchaseOrder
from products.models import SupplierProduct
from inventory.models import Inventory, InventoryMovement


# class BuyDropshippingProductsTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
#     def test_purchaseorder_inventory_received(self):
#         product = SupplierProduct.objects.get(
#             sku=SUPPLIER_WOODEN_CHAIR_SKU,
#             multi_tenant_company=self.multi_tenant_company)
#         inventory = Inventory.objects.filter(
#             multi_tenant_company=self.multi_tenant_company,
#             inventorylocation__precise=False,
#         ).first()
#
#         qty_original = product.inventory.physical()
#
#         purchase_order = PurchaseOrder.objects.\
#             filter(
#                 multi_tenant_company=self.multi_tenant_company).\
#             first()
#         po_item = purchase_order.purchaseorderitem_set.create(
#             multi_tenant_company=self.multi_tenant_company,
#             quantity=100,
#             product=product
#         )
#
#         qty_received = 10
#         location = inventory.inventorylocation
#         InventoryMovement.objects.create(
#             multi_tenant_company=self.multi_tenant_company,
#             movement_from=purchase_order,
#             product=product,
#             quantity=qty_received,
#             movement_to=location
#         )
#         po_item.refresh_from_db()
#         self.assertEqual(po_item.quantity_received, qty_received)
#         self.assertEqual(qty_original + qty_received, product.inventory.physical())
