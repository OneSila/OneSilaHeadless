from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from orders.models import SalesOrder, SalesOrderItem
from contacts.models import Customer

registry = DemoDataLibrary()


@registry.register_private_app
class SalesOrderGenerator(PrivateDataGenerator):
    model = SalesOrder
    count = 300
    field_mapper = {
        'reference': fake.order_reference,
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        customer = Customer.objects.filter(is_customer=True)

        kwargs['customer'] = customer
        kwargs['invoice_address'] = customer.invoice_address.last()
        kwargs['shipping_address'] = customer.shipping_address.last()
        return kwargs
