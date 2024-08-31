from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema
from currencies.currencies import currencies
from currencies.models import Currency
from products.models import SimpleProduct
from core.tests import TestCase
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class SalesPriceQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def get_currency_and_product_ids(self):
        simple_product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        simple_product_id = self.to_global_id(instance=simple_product)
        currency, _ = Currency.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
            **currencies['GB'])
        currency_id = self.to_global_id(instance=currency)

        return simple_product_id, currency_id

    def test_salesprice_none_prices(self):
        simple_product_id, currency_id = self.get_currency_and_product_ids()
        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            asserts_errors=False,
            query=mutation,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id}

            }}
        )

        self.assertTrue("You need to supply either RRP or Price." in str(resp.errors))

    def test_salesprice_rrp_only(self):
        simple_product_id, currency_id = self.get_currency_and_product_ids()
        rrp = 100.1

        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            asserts_errors=False,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id},
                "rrp": rrp,

            }}
        )
        self.assertEqual(resp.errors, None)
        rrp_received = float(resp.data['createSalesPrice']['rrp'])
        price_received = resp.data['createSalesPrice']['price']
        self.assertEqual(rrp_received, rrp)
        self.assertEqual(price_received, None)

    def test_salesprice_price_only(self):
        simple_product_id, currency_id = self.get_currency_and_product_ids()
        price = 200.1

        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            asserts_errors=False,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id},
                "price": price,

            }}
        )
        rrp_received = resp.data['createSalesPrice']['rrp']
        price_received = float(resp.data['createSalesPrice']['price'])
        self.assertEqual(rrp_received, None)
        self.assertEqual(price_received, price)

    def test_salesprice_both(self):
        simple_product_id, currency_id = self.get_currency_and_product_ids()
        rrp = 300.1
        price = 200.1

        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id},
                "price": price,
                "rrp": rrp,

            }}
        )
        rrp_received = float(resp.data['createSalesPrice']['rrp'])
        price_received = float(resp.data['createSalesPrice']['price'])
        self.assertEqual(rrp_received, rrp)
        self.assertEqual(price_received, price)

    def test_salesprice_rrp_lt_price(self):
        simple_product_id, currency_id = self.get_currency_and_product_ids()
        price = 300.1
        rrp = 200.1

        mutation = """
            mutation createSalesPrice($data: SalesPriceInput!) {
                createSalesPrice(data: $data) {
                  id
                  rrp
                  price
                }
              }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            asserts_errors=False,
            variables={'data': {
                "product": {"id": simple_product_id},
                "currency": {"id": currency_id},
                "price": price,
                "rrp": rrp,

            }}
        )
        self.assertTrue('Constraint “RRP cannot be less then the price” is violated.' in str(resp.errors))
        self.assertTrue(resp.errors is not None)
