from model_bakery import baker
from core.tests import TestCaseWithDemoData, TestCase, TransactionTestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class InventoryQueryTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
    def test_inventory_movements(self):
        from .queries import INVENTORY_MOVEMENTS_QUERY

        resp = self.strawberry_test_client(
            query=INVENTORY_MOVEMENTS_QUERY,
        )
        self.assertTrue(resp.errors is None)
        self.assertTrue(resp.data is not None)
