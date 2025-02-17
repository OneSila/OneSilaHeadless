from decimal import Decimal, ROUND_HALF_UP

from core.tests import TestCaseDemoDataMixin, TestCase
from products.models import Product
from products.demo_data import SIMPLE_CHAIR_WOOD_SKU
from accounting.models import Invoice
from accounting.factories.local_instance import InvoiceCreateFactory
from orders.tests.tests_factories.mixins import CreateTestOrderMixin

import logging

from taxes.models import VatRate

logger = logging.getLogger(__name__)


# class InvoiceCreateFactoryTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):
#
#     def test_invoice_creation_with_reference(self):
#         """
#         Test invoice creation when order already has a reference number.
#         """
#         product = Product.objects.get(sku=SIMPLE_CHAIR_WOOD_SKU, multi_tenant_company=self.multi_tenant_company)
#         vat_rate = VatRate.objects.filter(multi_tenant_company=self.multi_tenant_company).first()
#         product.vat_rate = vat_rate
#         product.save()
#
#         order_qty = 1
#         order = self.create_test_order('0000123', product, order_qty)
#
#         factory = InvoiceCreateFactory(instance=order)
#         factory.run()
#
#         invoice = Invoice.objects.filter(sales_order=order).first()
#
#         self.assertIsNotNone(invoice)
#         self.assertEqual(invoice.document_number, 'INV-0000001')
#         self.assertEqual(invoice.customer_name, order.customer.name)
#         # self.assertEqual(Decimal(order.total_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), invoice.subtotal + invoice.tax_amount)
#
#
#         # Verify the associated invoice items
#         invoice_items = invoice.items.all()
#         self.assertEqual(invoice_items.count(), 1)
#         item = invoice_items.first()
#         self.assertEqual(item.name, f"{product.name} ({product.sku})")
#         self.assertEqual(item.quantity, order_qty)
#         self.assertEqual(item.unit_price, Decimal(order.orderitem_set.first().price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
#         self.assertEqual(item.vat_rate, product.vat_rate)
#         # self.assertEqual(item.tax_amount, Decimal(item.unit_price * (item.preserved_vat_rate / 100)).quantize(Decimal('0.01'))) # this need improve is not that simple
