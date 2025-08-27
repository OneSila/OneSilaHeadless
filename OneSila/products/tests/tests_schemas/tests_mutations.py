from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.models import SimpleProduct, ProductTranslation, Product


DUPLICATE_PRODUCT_MUTATION = """
    mutation($product: ProductPartialInput!, $sku: String, $createAsAlias: Boolean) {
      duplicateProduct(product: $product, sku: $sku, createAsAlias: $createAsAlias) {
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
            variables={"product": {"id": self.to_global_id(self.product)}, "sku": None, "createAsAlias": False},
        )

        self.assertIsNone(resp.errors)
        data = resp.data["duplicateProduct"]
        self.assertIsNotNone(data["id"])

    def test_duplicate_product_mutation_existing_sku(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={"product": {"id": self.to_global_id(self.product)}, "sku": self.product.sku, "createAsAlias": False},
            asserts_errors=False,
        )

        self.assertTrue(resp.errors is not None)

    def test_duplicate_product_mutation_create_as_alias(self):
        resp = self.strawberry_test_client(
            query=DUPLICATE_PRODUCT_MUTATION,
            variables={"product": {"id": self.to_global_id(self.product)}, "sku": None, "createAsAlias": True},
        )

        self.assertIsNone(resp.errors)
        data = resp.data["duplicateProduct"]
        new_product = Product.objects.get(id=self.from_global_id(data["id"]))
        self.assertEqual(new_product.type, Product.ALIAS)
        self.assertEqual(new_product.alias_parent_product, self.product)
