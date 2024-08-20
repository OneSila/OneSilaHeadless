from core.tests import TestCaseDemoDataMixin, TestCase
from shipments.flows import prepare_shipments_flow
from orders.tests.tests_factories.mixins import CreateTestOrderMixin
from products.models import Product
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU
from core.helpers import save_test_file

import logging
logger = logging.getLogger(__name__)


class PickingListDocumentTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
    def test_picking_list(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 1
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        order.set_status_to_ship()

        prepare_shipments_flow(order)

        shipment = order.shipment_set.all().last()
        pdf = shipment.print()
        filepath = save_test_file('test_picking_list.pdf', pdf)

        logger.debug(F"File generated: {filepath}")
