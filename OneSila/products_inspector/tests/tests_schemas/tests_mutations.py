from unittest.mock import patch

from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import SimpleProduct


class BulkRefreshInspectorMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    @patch("products_inspector.tasks.products_inspector__tasks__bulk_refresh_inspector")
    def test_bulk_refresh_inspector(self, bulk_refresh_mock):
        product_one = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        product_two = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)

        mutation = """
            mutation BulkRefreshInspector($input: BulkRefreshInspectorInput!) {
              bulkRefreshInspector(instance: $input)
            }
        """
        variables = {
            "input": {
                "products": [
                    {"id": self.to_global_id(product_one)},
                    {"id": self.to_global_id(product_two)},
                ],
            },
        }

        resp = self.strawberry_test_client(query=mutation, variables=variables)

        self.assertIsNone(resp.errors)
        self.assertTrue(resp.data["bulkRefreshInspector"])