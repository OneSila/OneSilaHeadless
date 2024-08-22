from django.urls import reverse
from core.tests import TestCaseDemoDataMixin, TestCase
from shipments.flows import prepare_shipments_flow
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from products.models import Product
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU
from core.helpers import save_test_file

import logging
logger = logging.getLogger(__name__)


class OrderConfirmationTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    def test_confirmation(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 1
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        order.set_status_to_ship()

        filename, pdf = order.print()
        filepath = save_test_file(filename, pdf)

        logger.debug(F"File generated: {filepath}")

        url = reverse("orders:order_confirmation", kwargs={'pk': order.id})
        resp = self.client.get(url)
        self.assertTrue(resp.status_code, 200)
