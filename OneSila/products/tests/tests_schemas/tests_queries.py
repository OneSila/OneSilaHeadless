from django.test import TransactionTestCase
from products.models import SimpleProduct
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class SalesPriceQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_filters_test_simple_product(self):
        query = """
            query simpleProducts($sku: String!){
              simpleProducts(filters: {sku: {exact: $sku}}) {
                edges {
                  node {
                    id
                  }
                }
              }
            }
        """
        simple_product, _ = SimpleProduct.objects.get_or_create(sku='test_salesprice_none_prices',
            multi_tenant_company=self.multi_tenant_company)
        resp = self.strawberry_test_client(
            query=query,
            variables={"sku": simple_product.sku},
        )
        simple_product_id = resp.data['simpleProducts']['edges'][0]['node']['id']

        self.assertTrue(resp.errors is None)
