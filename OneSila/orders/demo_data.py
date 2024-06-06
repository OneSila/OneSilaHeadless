from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from currencies.models import Currency
from orders.models import Order, OrderItem
from contacts.models import Customer, InvoiceAddress, ShippingAddress
from products.models import Product
from django.utils import timezone
from random import randint

registry = DemoDataLibrary()


@registry.register_private_app
class SalesOrderGenerator(PrivateDataGenerator):
    model = Order
    count = 100
    field_mapper = {
        'reference': fake.order_reference,
        'status': lambda: fake.random_element(elements=(Order.DRAFT,
                                                        Order.PENDING,
                                                        Order.PENDING_INVENTORY,
                                                        Order.TO_PICK,
                                                        Order.TO_SHIP,
                                                        Order.DONE,
                                                        Order.CANCELLED,
                                                        Order.HOLD,
                                                        Order.EXCHANGED,
                                                        Order.REFUNDED,
                                                        Order.LOST,
                                                        Order.MERGED,
                                                        Order.DAMAGED,
                                                        Order.VOID))}

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']

        customer = Customer.objects.filter(is_customer=True, multi_tenant_company=multi_tenant_company).order_by('?').first()
        currency = Currency.objects.filter(iso_code__in=['GBP', 'USD', 'EUR', 'THB'], multi_tenant_company=multi_tenant_company).order_by('?').first()

        invoice_address = InvoiceAddress.objects.filter(company=customer, multi_tenant_company=multi_tenant_company).last()
        if not invoice_address:
            invoice_address = InvoiceAddress.objects.filter(multi_tenant_company=multi_tenant_company).first()

        shipping_address = ShippingAddress.objects.filter(company=customer, multi_tenant_company=multi_tenant_company).last()
        if not shipping_address:
            shipping_address = ShippingAddress.objects.filter(multi_tenant_company=multi_tenant_company).first()

        days_ago = randint(1, 50)
        new_created_at = timezone.now() - timezone.timedelta(days=days_ago)

        kwargs['customer'] = customer
        kwargs['currency'] = currency
        kwargs['created_at'] = new_created_at
        kwargs['invoice_address'] = invoice_address
        kwargs['shipping_address'] = shipping_address
        return kwargs


@registry.register_private_app
class OrderItemGenerator(PrivateDataGenerator):
    model = OrderItem
    count = 200

    field_mapper = {
        'quantity': lambda: fake.random_int(min=1, max=4),
        'price': lambda: round(fake.random_number(digits=2) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        order = Order.objects.filter(multi_tenant_company=multi_tenant_company).order_by('?').first()
        existing_product_ids = OrderItem.objects.filter(order=order, multi_tenant_company=multi_tenant_company).values_list('product_id', flat=True)
        product = Product.objects.filter(multi_tenant_company=multi_tenant_company).exclude(id__in=existing_product_ids).order_by('?').first()

        kwargs['product'] = product
        kwargs['order'] = order

        return kwargs
