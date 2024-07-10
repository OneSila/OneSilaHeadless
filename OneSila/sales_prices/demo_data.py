from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator
from faker.providers import BaseProvider
import random
from currencies.models import Currency
from products.models import Product
from .models import SalesPrice

registry = DemoDataLibrary()


class SalesPriceGenerator(PrivateDataGenerator):
    model = SalesPrice
    count = 1
    field_mapper = {}

    def set_product_qs(self):
        self.product_qs = Product.objects.\
            filter_multi_tenant(self.multi_tenant_company).\
            filter_has_prices()

    def set_currency(self):
        self.currency = Currency.objects.\
            filter_multi_tenant(self.multi_tenant_company).\
            get(is_default_currency=True)

    def generate(self):
        # We override the generate function as we'll just be adding prices
        # to all existing products found.
        self.set_product_qs()
        self.set_currency()

        for product in self.product_qs:
            base_kwargs = {
                'multi_tenant_company': self.multi_tenant_company,
                'currency': self.currency,
                'product': product,
            }

            salesprice, _ = SalesPrice.objects.get_or_create(**base_kwargs)
            salesprice.amount = fake.price()
            salesprice.discount_amount = fake.price_discount(salesprice.amount)
            salesprice.save()


registry.register_private_app(SalesPriceGenerator)
