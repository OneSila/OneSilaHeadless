from model_bakery import baker
from core.tests import TestCaseWithDemoData, TestCase, TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin

from products.models import SupplierProduct
from inventory.models import Inventory, InventoryLocation


class InventoryMutationTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
    def test_inventory_movements_mutation(self):
        from .mutations import INVENTORY_MOVEMENT_CREATE

        supplier_prod = SupplierProduct.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

        loc = InventoryLocation.objects.filter(multi_tenant_company=self.multi_tenant_company).first()
        loc_bis = InventoryLocation.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

        inv = Inventory.objects.create(multi_tenant_company=self.multi_tenant_company,
            quantity=10, inventorylocation=loc, product=supplier_prod)
        inv_bis = Inventory.objects.create(multi_tenant_company=self.multi_tenant_company,
            quantity=10, inventorylocation=loc_bis, product=supplier_prod)

        supplier_prod_id = self.to_global_id(supplier_prod)
        inv_id = self.to_global_id(inv)
        inv_bis_id = self.to_global_id(inv_bis)

        resp = self.strawberry_test_client(
            query=INVENTORY_MOVEMENT_CREATE,
            variables={'data': {
                'product': {'id': supplier_prod_id},
                'quantity': 5,
                'movementTo': {'id': inv_id},
                'movementFrom': {'id': inv_bis_id},
            }
            }
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
