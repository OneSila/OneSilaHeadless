from contacts.models import Company, Customer, ShippingAddress, InvoiceAddress, InternalCompany
from sales_prices.models import SalesPrice
from orders.models import Order

from contacts.demo_data import CUSTOMER_B2B

import logging
logger = logging.getLogger(__name__)


class CreateTestOrderMixin:
    def create_test_order(self, reference, product, quantity):
        customer = Customer.objects.get(multi_tenant_company=self.multi_tenant_company,
            name=CUSTOMER_B2B)
        shipping_address = ShippingAddress.objects.get(company=customer, multi_tenant_company=self.multi_tenant_company)
        invoice_address = InvoiceAddress.objects.get(company=customer, multi_tenant_company=self.multi_tenant_company)
        product_price = SalesPrice.objects.get(product=product, currency=customer.get_currency(), multi_tenant_company=self.multi_tenant_company)

        try:
            internal_company = InternalCompany.objects.get(multi_tenant_company=self.multi_tenant_company)
        except InternalCompany.DoesNotExist:
            internal_company = InternalCompany.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                name='Internal Company')

        logger.debug(f"test product has physical={product.inventory.physical()}")

        order = Order.objects.create(
            reference=reference,
            internal_company=internal_company,
            multi_tenant_company=self.multi_tenant_company,
            customer=customer,
            currency=customer.get_currency(),
            shipping_address=shipping_address,
            invoice_address=invoice_address)
        order.orderitem_set.create(product=product, quantity=quantity, price=product_price.get_real_price(), multi_tenant_company=self.multi_tenant_company)
        return order
