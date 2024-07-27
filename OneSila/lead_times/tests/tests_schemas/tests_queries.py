from django.test import TestCase, TransactionTestCase
from model_bakery import baker

from OneSila.schema import schema

from core.tests import TestCaseWithDemoData
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class LeadTimeQueriesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_lead_time_units(self):
        query = """
            query leadTimeUnits {
                leadTimeUnits {
                    edges {
                        node {
                            code
                            name
                        }
                    }
                }
            }
        """
        resp = self.straberry_test_client(
            query=query,
            assert_errors=False,
        )
        self.assertTrue(resp.errors is None)


# class AddressTestCase(TestCaseWithDemoData, TransactionTestCaseMixin, TransactionTestCase):
#     def setUp(self):
#         super().setUp()
#         self.addresses = Address.objects.filter(multi_tenant_company=self.user.multi_tenant_company)

#     def test_addresses(self):
#         query = """
#             query addresses {
#               addresses {
#                 edges {
#                   node {
#                     id
#                     fullAddress
#                   }
#                 }
#                 totalCount
#               }
#             }
#         """

#         resp = self.stawberry_test_client(
#             query=query,
#         )
#         self.assertTrue(resp.errors is None)
#         self.assertTrue(resp.data is not None)

#         total_count = resp.data['addresses']['totalCount']
#         self.assertEqual(total_count, len(self.addresses))
