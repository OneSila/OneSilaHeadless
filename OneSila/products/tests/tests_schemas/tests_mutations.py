from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import SimpleProduct, ProductTranslation


DUPLICATE_PRODUCT_MUTATION = """
    mutation($product: ProductPartialInput!, $sku: String) {
      duplicateProduct(product: $product, sku: $sku) {
        id
        sku
      }
    }
"""


class DuplicateProductMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Original",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_duplicate_product_mutation(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={"product": {"id": self.to_global_id(self.product)}, "sku": None},
        )

        self.assertIsNone(resp.errors)
        data = resp.data["duplicateProduct"]
        self.assertIsNotNone(data["id"])

    def test_duplicate_product_mutation_existing_sku(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={"product": {"id": self.to_global_id(self.product)}, "sku": self.product.sku},
            asserts_errors=False,
        )

        self.assertTrue(resp.errors is not None)
