from core.tests import TestCase
from lead_times.models import LeadTime


class LeadTimeManagerTestCase(TestCase):
    def test_filter_fastest(self):
        lead_time_fast, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=4, unit=LeadTime.HOUR)
        lead_time_overlap, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=2, max_time=5, unit=LeadTime.HOUR)
        lead_time_slow, _ = LeadTime.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            min_time=1, max_time=2, unit=LeadTime.DAY)

        filtered = LeadTime.objects.\
            filter_fastest([lead_time_fast.id, lead_time_overlap.id, lead_time_slow.id])

        self.assertEqual(filtered, lead_time_fast)
