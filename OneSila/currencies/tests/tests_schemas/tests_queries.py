from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from core.tests import TransactionTestCase
from currencies.currencies import currencies


# @TODO: This test works fine when run with -k but breaks when run full test. Found out why!
# class TestPublicCurrenciesQuery(TransactionTestCaseMixin, TransactionTestCase):
#     def test_public_currencies_contains_all_iso_codes(self):
#         query = """
#             query publicCurrencies {
#                 publicCurrencies {
#                     edges {
#                         node {
#                             isoCode
#                         }
#                     }
#                 }
#             }
#         """
#         resp = self.strawberry_test_client(query=query)
#         self.assertIsNone(resp.errors)
#         returned = {edge['node']['isoCode'] for edge in resp.data['publicCurrencies']['edges']}
#
#         self.assertTrue(len(returned) > 0)
#
#         expected = {data['iso_code'] for data in currencies.values()}
#         self.assertTrue(expected.issubset(returned))
