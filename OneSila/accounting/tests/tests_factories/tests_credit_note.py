from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from core.tests import TestCaseDemoDataMixin, TestCase
from products.models import Product
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU
from accounting.models import CreditNote
from accounting.factories.local_instance import CreditNoteCreateFactory
from orders.tests.tests_factories.mixins import CreateTestOrderMixin

import logging
from taxes.models import VatRate
from order_returns.models import OrderReturn, OrderReturnItem

logger = logging.getLogger(__name__)


class CreditNoteCreateFactoryTestCase(CreateTestOrderMixin, TestCaseDemoDataMixin, TestCase):

    def test_credit_note_creation_with_reference(self):
        """
        Test credit note creation when return already has a reference number.
        """
        product = Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company)
        vat_rate = VatRate.objects.filter(multi_tenant_company=self.multi_tenant_company).first()
        product.vat_rate = vat_rate
        product.save()

        order_qty = 2
        return_qty = 1
        order = self.create_test_order('INV-1234567', product, order_qty)

        # Create the return
        order_return = OrderReturn.objects.create(multi_tenant_company=order.multi_tenant_company, order=order, received_on=timezone.now().date())
        OrderReturnItem.objects.create(multi_tenant_company=order.multi_tenant_company, order_return=order_return, order_item=order.orderitem_set.first(), product=product, quantity=return_qty)

        factory = CreditNoteCreateFactory(instance=order_return)
        factory.run()

        credit_note = CreditNote.objects.filter(order_return=order_return).first()

        self.assertIsNotNone(credit_note)
        self.assertNotEquals(credit_note.document_number, 'INV-1234567')
        self.assertEqual(credit_note.customer_name, order.customer.name)
        self.assertEqual(Decimal(order_return.total_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), credit_note.subtotal + credit_note.tax_amount)


        # Verify the associated credit note items
        credit_note_items = credit_note.items.all()
        self.assertEqual(credit_note_items.count(), 1)
        item = credit_note_items.first()
        self.assertEqual(item.name, f"{product.name} ({product.sku})")
        self.assertEqual(item.quantity, return_qty)
        self.assertEqual(item.unit_price, Decimal(order.orderitem_set.first().price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        self.assertEqual(item.vat_rate, product.vat_rate)
        self.assertEqual(item.tax_amount, Decimal(item.unit_price * (item.preserved_vat_rate / 100)).quantize(Decimal('0.01')))