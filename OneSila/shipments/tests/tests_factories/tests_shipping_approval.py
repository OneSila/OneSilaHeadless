from core.tests import TestCase, TestWithDemoDataMixin
from core.exceptions import SanityCheckError
from shipments.factories import PreApproveShippingFactory
from orders.models import Order
from contacts.demo_data import CUSTOMER_B2B
from contacts.models import Customer, ShippingAddress, InvoiceAddress
from products.models import Product
from sales_prices.models import SalesPrice
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU, BUNDLE_PEN_AND_INK_SKU
from .mixins import CreateTestOrderMixin

import logging
logger = logging.getLogger(__name__)


class TestPreApproveShippingFactory(CreateTestOrderMixin, TestWithDemoDataMixin, TestCase):
    def test_pre_approve_shipping_in_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 1
        order = self.create_test_order('test_pre_approve_shipping_in_stock', product, order_qty)
        order.set_status_processing()

        with self.assertRaises(SanityCheckError):
            f = PreApproveShippingFactory(order)
            f.run()

    def test_pre_approve_shipping_in_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 1
        order = self.create_test_order('test_pre_approve_shipping_in_stock', product, order_qty)
        order.set_status_pending_shipping()

        f = PreApproveShippingFactory(order)
        f.run()

        self.assertTrue(order.is_to_ship())

    def test_pre_approve_shipping_partial_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order_qty = 15
        order = self.create_test_order('test_prepare_shipment', product, order_qty)
        order.set_status_pending_shipping()

        f = PreApproveShippingFactory(order)
        f.run()

        self.assertTrue(order.is_pending_shipping_approval())
