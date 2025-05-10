

from .mixins import TestCaseWoocommerceMixin
from django.conf import settings

from sales_channels.integrations.woocommerce.tests.helpers import CreateTestProductMixin
from sales_channels.integrations.woocommerce.factories.pulling import WoocommerceRemoteCurrencyPullFactory

import logging
logger = logging.getLogger(__name__)


class TestWoocommerceRemoteCurrencyPullFactory(CreateTestProductMixin, TestCaseWoocommerceMixin):
    def test_pull_remote_currency(self):
        factory = WoocommerceRemoteCurrencyPullFactory(
            sales_channel=self.sales_channel
        )
        factory.run()
