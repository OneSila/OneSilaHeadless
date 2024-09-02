from django.urls import reverse
from core.tests import TestCaseDemoDataMixin, TestCase
from shipments.models import Shipment
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from products.models import Product
from products.demo_data import SIMPLE_PEN_SKU
from core.helpers import save_test_file

import logging
logger = logging.getLogger(__name__)


class PickingListDocumentTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    def test_picking_list(self):
        product = Product.objects.get(sku=SIMPLE_PEN_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 1
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        order.set_status_pending_processing()
        self.assertEqual(order.status, order.SHIPPED)

        shipment = Shipment.objects.last()

        filename, pdf = shipment.print()
        filepath = save_test_file(filename, pdf)

        logger.debug(F"File generated: {filepath}")

        url = reverse("shipments:shipment_pickinglist", kwargs={'pk': shipment.id})
        resp = self.client.get(url)
        self.assertTrue(resp.status_code, 200)
