from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from currencies.models import Currency
from orders.models import Order, OrderItem
from contacts.models import Customer, InvoiceAddress, ShippingAddress
from products.models import Product

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
        customer = Customer.objects.filter(is_customer=True).order_by('?').first()
        currency = Currency.objects.filter(iso_code__in=['GBP', 'USD', 'EUR', 'THB']).order_by('?').first()

        invoice_address = InvoiceAddress.objects.filter(company=customer).last()
        if not invoice_address:
            invoice_address = InvoiceAddress.objects.first()

        shipping_address = ShippingAddress.objects.filter(company=customer).last()
        if not shipping_address:
            shipping_address = ShippingAddress.objects.first()

        kwargs['customer'] = customer
        kwargs['currency'] = currency
        kwargs['invoice_address'] = invoice_address
        kwargs['shipping_address'] = shipping_address
        return kwargs


@registry.register_private_app
class OrderItemGenerator(PrivateDataGenerator):
    model = OrderItem
    count = 1000

    field_mapper = {
        'quantity': lambda: fake.random_int(min=1, max=4),
        'price': lambda: round(fake.random_number(digits=2) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        super_kwargs = super().prep_baker_kwargs(seed)
        valid = False
        attempts = 0
        max_attempts = 5

        while not valid and attempts < max_attempts:
            product = Product.objects.order_by('?').first()
            order = Order.objects.order_by('?').first()

            # Check if the combination already exists
            if not OrderItem.objects.filter(order=order, product=product).exists():
                valid = True
                super_kwargs['product'] = product
                super_kwargs['order'] = order
            attempts += 1

        return super_kwargs
