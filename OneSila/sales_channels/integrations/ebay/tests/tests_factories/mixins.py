from datetime import timedelta

from django.utils import timezone

from core.tests import TransactionTestCase
from sales_channels.integrations.ebay.models import EbaySalesChannel


class TestCaseEbayMixin(TransactionTestCase):
    def setUp(self):
        super().setUp()
        refresh_expiration = timezone.now() + timedelta(days=1)
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname='test.ebay',
            environment=EbaySalesChannel.PRODUCTION,
            active=True,
            multi_tenant_company=self.multi_tenant_company,
            refresh_token='test-refresh-token',
            refresh_token_expiration=refresh_expiration,
        )
