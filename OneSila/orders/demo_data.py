from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator, \
    PrivateStructuredDataGenerator
from currencies.models import Currency
from contacts.models import Customer, InternalCompany
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

    def get_product(self, sku):
        return Product.objects.get(sku=sku, multi_tenant_company=self.multi_tenant_company)

    def get_currency(self, customer_name):
        return self.get_customer(customer_name).get_currency()

    def get_internal_company(self):
        try:
            internal_company = InternalCompany.objects.get(multi_tenant_company=self.multi_tenant_company)
        except InternalCompany.DoesNotExist:
            internal_company = InternalCompany.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                name='Internal Company')

        return internal_company

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'reference': 'Demo Order AF192',
                    'customer': self.get_customer(CUSTOMER_B2B),
                    'currency': self.get_currency(CUSTOMER_B2B),
                    'invoice_address': InvoiceAddress.objects.get(company=self.get_customer(CUSTOMER_B2B), multi_tenant_company=self.multi_tenant_company),
                    'shipping_address': ShippingAddress.objects.get(company=self.get_customer(CUSTOMER_B2B), multi_tenant_company=self.multi_tenant_company),
                    'created_at': self.get_created_at(),
                    'internal_company': self.get_internal_company(),
                },
                'post_data': {
                    'orderitem_set': [
                        {
                            'product': self.get_product(SIMPLE_BLACK_FABRIC_PRODUCT_SKU),
                            'quantity': 1,
                            'price': self.get_product(SIMPLE_BLACK_FABRIC_PRODUCT_SKU).salesprice_set.get(currency=self.get_currency(CUSTOMER_B2B)).get_real_price(),
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
        instance.set_status_pending_processing()
