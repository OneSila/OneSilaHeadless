# from core.tests import TestCase
# from products.models import Product, SimpleProduct, SupplierProduct
# from contacts.models import Supplier
# from inventory.models import Inventory, InventoryLocation

# class InventoryUpdateTriggerFactoryTestCase(TestCase):
#     def test_inventory_trigger_with_simple(self):
#         # verify that inventory changes are emitted thought the
#         # parent product structure.
#         supplier = Supplier.objects.create(multi_tenant_company=self.multi_tenant_company)
#         supplier_product = SupplierProduct.objects.create(multi_tenant_company=self.multi_tenant_company,
#             sku='fake-1i281', supplier=supplier)
#         simple_product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
#         simple_product.supplier_products.add(supplier_product)

#         loc = InventoryLocation.objects.create(multi_tenant_company=self.multi_tenant_company,
#             shippingaddress=self.multi_tenant_company.address_set.last())
#         Inventory.objects.create(inventory_location=loc,
#             quantity=199)
