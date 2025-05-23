from sales_channels.integrations.woocommerce.factories.pulling import WoocommerceRemoteCurrencyPullFactory, \
    WoocommerceSalesChannelViewPullFactory, WoocommerceLanguagePullFactory
from sales_channels.integrations.woocommerce.models import WoocommerceCurrency, WoocommerceSalesChannel
from core.tests import TransactionTestCase
from django.conf import settings

from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel

import logging
logger = logging.getLogger(__name__)


class TestCaseWoocommerceMixin(TransactionTestCase):
    def setUp(self):
        """
        Set up the test case with a mock WoocommerceSalesChannel.
        """
        super().setUp()
        self.test_store_settings = settings.SALES_CHANNELS_INTEGRATIONS_TEST_STORES['WOOCOMMERCE']
        self.sales_channel = WoocommerceSalesChannel.objects.create(
            hostname=self.test_store_settings['hostname'],
            api_url=self.test_store_settings['hostname'] + "/wp-json",
            api_key=self.test_store_settings['api_key'],
            api_secret=self.test_store_settings['api_secret'],
            api_version=self.test_store_settings['api_version'],
            timeout=self.test_store_settings.get('timeout', 10),
            verify_ssl=self.test_store_settings.get('verify_ssl', False),
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        pull_factory = WoocommerceRemoteCurrencyPullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        pull_factory = WoocommerceSalesChannelViewPullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        pull_factory = WoocommerceLanguagePullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        self.api = pull_factory.get_api()

        remote_currency = WoocommerceCurrency.objects.get(
            sales_channel=self.sales_channel,
        )
        remote_currency.local_instance = self.currency
        remote_currency.save()

    def tearDown(self):
        try:
            from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttribute, \
                WoocommerceProduct

            attribute_ids = WoocommerceGlobalAttribute.objects.filter(sales_channel=self.sales_channel).values_list('remote_id', flat=True)
            product_ids = WoocommerceProduct.objects.filter(sales_channel=self.sales_channel).values_list('remote_id', flat=True)

            for attribute_id in attribute_ids:
                self.api.delete_attribute(attribute_id)

            for product_id in product_ids:
                self.api.delete_product(product_id)

        except AttributeError:
            logger.warning("No api set. Cleanup is not possible.")
            pass
