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
                code
                name
              }
            }
        """
        resp = self.strawberry_anonymous_test_client(
            query=query,
        )
        self.assertTrue(resp.errors is None)
