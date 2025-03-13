from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator, \
    PrivateStructuredDataGenerator
from currencies.models import Currency
from contacts.models import Customer, InternalCompany
from orders.models import Order, OrderItem
from contacts.models import Customer, InvoiceAddress, ShippingAddress
from products.models import Product
from django.utils import timezone
from random import randint
from products.demo_data import SIMPLE_CHAIR_WOOD_SKU
from contacts.demo_data import CUSTOMER_B2B

registry = DemoDataLibrary()


@registry.register_private_app
class SalesOrderGenerator(PrivateStructuredDataGenerator):
    model = Order

    def get_created_at(self):
        days_ago = randint(1, 50)
        return timezone.now() - timezone.timedelta(days=days_ago)

    def get_product(self, sku):
        return Product.objects.get(sku=sku, multi_tenant_company=self.multi_tenant_company)

    def get_currency(self, customer_name):
        return Currency.objects.filter(multi_tenant_company=self.multi_tenant_company, is_default_currency=True).first()

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'reference': 'Demo Order AF192',
                    'currency': self.get_currency(CUSTOMER_B2B),
                    'created_at': self.get_created_at(),
                },
                'post_data': {
                    'orderitem_set': [
                        {
                            'product': self.get_product(SIMPLE_CHAIR_WOOD_SKU),
                            'quantity': 1,
                            'price': self.get_product(SIMPLE_CHAIR_WOOD_SKU).salesprice_set.get(currency=self.get_currency(CUSTOMER_B2B)).get_real_price(),
                        },
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
