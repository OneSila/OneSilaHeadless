from core.tests import TestCase, TestCaseDemoDataMixin
from core.exceptions import SanityCheckError
from shipments.factories import PreApproveShippingFactory
from orders.models import Order
from contacts.demo_data import CUSTOMER_B2B
from contacts.models import Customer, ShippingAddress, InvoiceAddress
from products.models import Product
from sales_prices.models import SalesPrice
from products.demo_data import SIMPLE_CHAIR_WOOD_SKU, BUNDLE_DINING_SET_SKU
from .mixins import CreateTestOrderMixin

import logging
logger = logging.getLogger(__name__)


# class TestPreApproveShippingFactory(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
#     def test_pre_approve_shipping_in_stock_draft_status(self):
#         product = Product.objects.get(sku=SIMPLE_CHAIR_WOOD_SKU, multi_tenant_company=self.multi_tenant_company)
#         order_qty = 1
#         order = self.create_test_order('test_pre_approve_shipping_in_stock_draft_status', product, order_qty)
#         order.set_status_draft()
#
#         with self.assertRaises(SanityCheckError):
#             f = PreApproveShippingFactory(order)
#             f.run()
#
#     def test_pre_approve_shipping_in_stock(self):
#         product = Product.objects.get(sku=SIMPLE_CHAIR_WOOD_SKU, multi_tenant_company=self.multi_tenant_company)
#         order_qty = 1
#         order = self.create_test_order('test_pre_approve_shipping_in_stock', product, order_qty)
#         order.set_status_pending_processing()
#
#         self.assertEqual(order.SHIPPED, order.status)
#
#     def test_pre_approve_shipping_partial_stock_factory(self):
#         product = Product.objects.get(sku=SIMPLE_CHAIR_WOOD_SKU, multi_tenant_company=self.multi_tenant_company)
#         order_qty = 15
#         order = self.create_test_order('test_prepare_shipment', product, order_qty)
#         order.set_status_pending_processing()
#
#         self.assertEqual(order.PENDING_SHIPPING_APPROVAL, order.status)
