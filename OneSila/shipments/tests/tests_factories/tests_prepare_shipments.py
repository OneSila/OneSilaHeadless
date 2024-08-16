from core.tests import TestCase, TestWithDemoDataMixin
from shipments.factories import PrepareShipmentsFactory
from orders.models import Order
from contacts.demo_data import CUSTOMER_B2B
from contacts.models import Customer, ShippingAddress, InvoiceAddress


class TestPrepareShipmentFactory(TestWithDemoDataMixin, TestCase):
    def test_prepare_shipment(self):
        customer = Customer.objects.get(multi_tenant_company=self.multi_tenant_company,
            name=CUSTOMER_B2B)
        shipping_address = ShippingAddress.objects.get(customer=customer, multi_tenant_company=self.multi_tenant_company)
        invoice_address = InvoiceAddress.objects.get(customer=customer, multi_tenant_company=self.multi_tenant_company)
        order = Order.objects.create(
            reference='test_prepare_shipment',
            multi_tenant_company=self.multi_tenant_company,
            status=Order.TO_SHIP,
            orderitem__isnull=False,
            customer=customer,
            shipping_address=shipping_address,
            invoice_address=invoice_address)

        f = PrepareShipmentsFactory(order)
        f.run()
