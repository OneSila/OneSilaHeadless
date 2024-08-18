from core.tests import TestCase, TestWithDemoDataMixin
from core.exceptions import SanityCheckError
from shipments.factories import PrepareShipmentsFactory
from orders.models import Order
from contacts.demo_data import CUSTOMER_B2B
from contacts.models import Customer, ShippingAddress, InvoiceAddress
from products.models import Product
from sales_prices.models import SalesPrice
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU, BUNDLE_PEN_AND_INK_SKU

import logging
logger = logging.getLogger(__name__)


class TestPrepareShipmentFactory(TestWithDemoDataMixin, TestCase):
    def create_test_order(self, reference, product, quantity):
        customer = Customer.objects.get(multi_tenant_company=self.multi_tenant_company,
            name=CUSTOMER_B2B)
        shipping_address = ShippingAddress.objects.get(company=customer, multi_tenant_company=self.multi_tenant_company)
        invoice_address = InvoiceAddress.objects.get(company=customer, multi_tenant_company=self.multi_tenant_company)
        product_price = SalesPrice.objects.get(product=product, currency=customer.get_currency(), multi_tenant_company=self.multi_tenant_company)

        logger.debug(f"test product has physical={product.inventory.physical()}")

        order = Order.objects.create(
            reference=reference,
            multi_tenant_company=self.multi_tenant_company,
            customer=customer,
            currency=customer.get_currency(),
            shipping_address=shipping_address,
            invoice_address=invoice_address)
        order.orderitem_set.create(product=product, quantity=quantity, price=product_price.get_real_price(), multi_tenant_company=self.multi_tenant_company)
        return order

    def test_prepare_shipment_sanity_check(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_prepare_shipment', product, 1)
        order.set_status_processing()

        with self.assertRaises(SanityCheckError):
            f = PrepareShipmentsFactory(order)
            f.run()

    def test_prepare_shipment_all_on_stock_simple_single_supplier_product(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_prepare_shipment', product, 1)
        order.set_status_to_ship()

        f = PrepareShipmentsFactory(order)
        f.run()

        self.assertTrue(f.shipments is not None)
        self.assertTrue(f.shipmentitems is not None)
        self.assertEqual(len(f.shipmentitems), 1)
        self.assertEqual(f.shipmentitems[0].quantity, 1)

    def test_prepare_shipment_all_on_stock_bundle(self):
        product = Product.objects.get(sku=BUNDLE_PEN_AND_INK_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_prepare_shipment', product, 1)
        order.set_status_to_ship()

        logger.debug(f"{order=} with {order.orderitem_set.all()}")

        f = PrepareShipmentsFactory(order)
        f.run()

        self.assertTrue(f.shipments is not None)
        self.assertTrue(f.shipmentitems is not None)
        # The Pen bundle consists out of 1 pen and 6 cartridges
        logger.debug(f.shipmentitems)
        logger.debug(f.shipmentitems[0].quantity)
        shipped_items = sum([i.quantity for i in f.shipmentitems])
        self.assertEqual(shipped_items, 7)
        # The pen and some of the cartridges are on location one
        # the rest of the ink cartridges are on another location
        self.assertEqual(len(f.shipments), 2)

    def test_prepare_shipment_all_not_all_on_stock(self):
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        order = self.create_test_order('test_prepare_shipment', product, 15)
        order.set_status_to_ship()

        with self.assertRaises(SanityCheckError):
            f = PrepareShipmentsFactory(order)
            f.run()
