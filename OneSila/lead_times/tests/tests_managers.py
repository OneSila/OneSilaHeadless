from core.tests import TestCase, TestCaseDemoDataMixin
from contacts.models import ShippingAddress, Supplier
from lead_times.models import LeadTime


class LeadTimeManagerTestCase(TestCaseDemoDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.lead_time_fast, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=4, unit=LeadTime.HOUR)
        self.lead_time_overlap, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=2, max_time=5, unit=LeadTime.HOUR)
        self.lead_time_slow, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=2, unit=LeadTime.DAY)
        self.supplier = Supplier.objects.create(name="Supplier Company", multi_tenant_company=self.multi_tenant_company)
        self.shipping_address = ShippingAddress.objects.create(multi_tenant_company=self.multi_tenant_company, company=self.supplier)

    def test_filter_fastest(self):
        filtered = LeadTime.objects.\
            filter_fastest([self.lead_time_fast.id, self.lead_time_overlap.id, self.lead_time_slow.id])

        self.assertEqual(filtered, self.lead_time_fast)

    def test_filter_fastest_qs(self):
        filtered = LeadTime.objects.filter(multi_tenant_company=self.multi_tenant_company)
        fastest = filtered.filter_fastest()

        self.assertEqual(fastest, self.lead_time_fast)