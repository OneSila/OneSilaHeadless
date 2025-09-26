from core.tests import TransactionTestCase
from sales_channels.integrations.ebay.models import EbaySalesChannel


class TestCaseEbayMixin(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname='test.ebay',
            environment=EbaySalesChannel.PRODUCTION,
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        )
