from core.tests import TestCase
from django.conf import settings

from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


class TestCaseWoocommerceMixin(TestCase):
    def setUp(self):
        """
        Set up the test case with a mock WoocommerceSalesChannel.
        """
        self.test_store_settings = settings.SALES_CHANNELS_INTEGRATIONS_TEST_STORES['WOOCOMMERCE']
        self.sales_channel = WoocommerceSalesChannel.objects.create(
            hostname=self.test_store_settings['hostname'],
            api_url=self.test_store_settings['hostname'] + "/wp-json",
            api_key=self.test_store_settings['api_key'],
            api_secret=self.test_store_settings['api_secret'],
            api_version=self.test_store_settings['api_version'],
            timeout=self.test_store_settings.get('timeout', 10),
            verify_ssl=self.test_store_settings.get('verify_ssl', False)
        )
        super().setUp()
