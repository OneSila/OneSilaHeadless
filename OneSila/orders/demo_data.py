from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator, \
    PrivateStructuredDataGenerator
from currencies.models import Currency
from contacts.models import Customer
from orders.models import Order, OrderItem
from contacts.models import Customer, InvoiceAddress, ShippingAddress
from products.models import Product
from django.utils import timezone
from random import randint
from products.demo_data import SIMPLE_BLACK_FABRIC_PRODUCT_SKU
from contacts.demo_data import CUSTOMER_B2B

registry = DemoDataLibrary()


@registry.register_private_app
class SalesOrderGenerator(PrivateStructuredDataGenerator):
    model = Order

    def get_customer(self, name):
        return Customer.objects.get(name=name, multi_tenant_company=self.multi_tenant_company)

    def get_created_at(self):
        days_ago = randint(1, 50)
        return timezone.now() - timezone.timedelta(days=days_ago)

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'reference': 'Demo Order AF192',
                    'customer': self.get_customer(CUSTOMER_B2B),
                    'currency': Currency.objects.get(is_default_currency=True, multi_tenant_company=self.multi_tenant_company),
                    'invoice_address': InvoiceAddress.objects.get(company=self.get_customer(CUSTOMER_B2B), multi_tenant_company=self.multi_tenant_company),
                    'shipping_address': ShippingAddress.objects.get(company=self.get_customer(CUSTOMER_B2B), multi_tenant_company=self.multi_tenant_company),
                    'created_at': self.get_created_at(),
                },
                'post_data': {
                    'orderitem_set': [
                        {
                            'product': Product.objects.get(sku=SIMPLE_BLACK_FABRIC_PRODUCT_SKU, multi_tenant_company=self.multi_tenant_company),
                            'quantity': 1,
                        }
                    ]

                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        items = kwargs['orderitem_set']
        for item in items:
            instance.orderitem_set.create(
                multi_tenant_company=self.multi_tenant_company,
                **item
            )
