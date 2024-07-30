from core.tests import TestCase, TransactionTestCase, \
    TransactionTestCaseMixin, TestWithDemoDataMixin
from model_bakery import baker
from OneSila.schema import schema
from lead_times.models import LeadTime
from contacts.models import ShippingAddress


class LeadTimeQueriesTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_lead_time_create(self):
        query = """
            mutation createLeadTime($name: String!, $unit: Int!, $minTime: Int!, $maxTime: Int!) {
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
        name = "Delivery <2 hours test"

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


class LeadTimeForShippingAddressTestCase(TestWithDemoDataMixin, TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.lead_time, _ = LeadTime.objects.get_or_create(min_time=1, max_time=10, unit=LeadTime.DAY,
            multi_tenant_company=self.multi_tenant_company)
        self.shipping_address = ShippingAddress.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

    def test_leadtime_for_shippingaddress(self):
        from .mutations import create_leadtime_for_shippingaddress
        from lead_times.schema.types.types import LeadTimeForShippingAddressType, LeadTimeType
        shippingid = self.to_global_id(instance=self.shipping_address)
        leadtimeid = self.to_global_id(instance=self.lead_time)

        resp = self.strawberry_test_client(
            query=create_leadtime_for_shippingaddress,
            variables={'shippingid': shippingid, 'leadtimeid': leadtimeid})
        self.assertTrue(resp.errors is None)
