from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from core.tests import TransactionTestCase
from currencies.currencies import currencies


class TestPublicCurrenciesQuery(TransactionTestCaseMixin, TransactionTestCase):
    def test_public_currencies_contains_all_iso_codes(self):
        query = """
            query publicCurrencies {
                publicCurrencies {
                    edges {
                        node {
                            isoCode
                        }
                    }
                }
            }
        """
        resp = self.strawberry_anonymous_test_client(query=query)
        self.assertIsNone(resp.errors)

        returned = {edge['node']['isoCode'] for edge in resp.data['publicCurrencies']['edges']}
        expected = {data['iso_code'] for data in currencies.values()}
        self.assertTrue(expected.issubset(returned))
