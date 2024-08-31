from model_bakery import baker
from core.tests import TestCaseWithDemoData, TestCase, TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class InventoryQueryTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
    def test_inventory_movements(self):
        query = """
            query inventoryMovements {
              inventoryMovements {
                edges {
                  node {
                    id
                    movementFrom {id}
                    movementTo {id}
                    product {id}
                    quantity
                    notes
                  }
                }
                totalCount
              }
            }
        """

        resp = self.strawberry_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
        self.assertEqual(total_count, len(self.addresses))
