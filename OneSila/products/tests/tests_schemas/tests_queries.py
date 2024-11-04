from django.test import TransactionTestCase
from products.models import SimpleProduct
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class ProductQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_filters_test_simple_product(self):
        from .queries import SIMPLE_PRODUCT_SKU_FILTER
        simple_product, _ = SimpleProduct.objects.get_or_create(sku='test_salesprice_none_prices',
            multi_tenant_company=self.multi_tenant_company)
        resp = self.strawberry_test_client(
            query=SIMPLE_PRODUCT_SKU_FILTER,
            variables={"sku": simple_product.sku},
        )
        self.assertTrue(resp.errors is None)

    def test_search_product(self):
        from .queries import PRODUCT_SEARCH
        resp = self.strawberry_test_client(
            query=PRODUCT_SEARCH,
            variables={"search": 'some product'},
        )
        self.assertTrue(resp.errors is None)


    def test_exclude_demo_data_product(self):
        from .queries import PRODUCT_EXCLUDE_DEMO_DATA

        resp = self.strawberry_test_client(
            query=PRODUCT_EXCLUDE_DEMO_DATA,
            variables={"excludeDemoData": True},
        )

        self.assertTrue(resp.errors is None)