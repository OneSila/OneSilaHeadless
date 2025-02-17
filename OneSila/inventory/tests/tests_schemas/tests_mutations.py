from model_bakery import baker
from core.tests import TestCaseWithDemoData, TestCase, TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin

from products.models import SupplierProduct
from inventory.models import Inventory, InventoryLocation

#
# class InventoryMutationTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
#     def test_inventory_movements_mutation(self):
#         from .mutations import INVENTORY_MOVEMENT_CREATE
#
#         supplier_prod = SupplierProduct.objects.filter(multi_tenant_company=self.multi_tenant_company).last()
#
#         loc = InventoryLocation.objects.filter(multi_tenant_company=self.multi_tenant_company).first()
#         loc_bis = InventoryLocation.objects.filter(multi_tenant_company=self.multi_tenant_company, precise=False).last()
#
#         self.assertTrue(loc is not None)
#         self.assertTrue(loc_bis is not None)
#
#         supplier_prod_id = self.to_global_id(supplier_prod)
#         loc_id = self.to_global_id(loc)
#         loc_bis_id = self.to_global_id(loc_bis)
#
#         inv = loc.inventory_set.create(
#             multi_tenant_company=self.multi_tenant_company,
#             product=supplier_prod,
#             quantity=5
#         )
#
#         resp = self.strawberry_test_client(
#             query=INVENTORY_MOVEMENT_CREATE,
#             variables={'data': {
#                 'product': {'id': supplier_prod_id},  # GlobalID
#                 'quantity': 5,
#                 'movementFromId': loc_id,
#                 'movementToId': loc_bis_id,
#                 }
#             }
#         )
#
#         self.assertTrue(resp.errors is None)
#         self.assertTrue(resp.data is not None)
