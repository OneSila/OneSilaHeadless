from django.test import TestCase, TransactionTestCase
from model_bakery import baker
from OneSila.schema import schema
from core.tests import TestCaseWithDemoData
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from lead_times.models import LeadTime


class LeadTimeQueriesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_lead_time_create(self):
        query = """
            mutation createLeadTime($name: String!, $unit: String!, $minTime: Int!, $maxTime: Int!) {
              createLeadTime(
                data: {unit: $unit, minTime: $minTime, maxTime: $maxTime, name: $name}
              ) {
                id
                unit
                name
              }
            }
        """
        unit = LeadTime.HOUR
        min_time = 1
        max_time = 2
        name = "Delivery <2 hours"

        resp = self.strawberry_test_client(
            query=query,
            variables={
                'unit': unit,
                'minTime': min_time,
                'maxTime': max_time,
                'name': name,
            },
        )
        self.assertTrue(resp.errors is None)
        self.assertEqual(resp.data['createLeadTime']['name'], name)
