from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, \
    PrivateStructuredDataGenerator
from currencies.models import Currency
from products.models import Product
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from datetime import datetime

registry = DemoDataLibrary()


# @registry.register_private_app
# class SalesPriceDemoDataGenerator(PrivateStructuredDataGenerator)
#     model = SalesPrice

#     def get_structure(self):
#         return [
#             {
#                 'instance_data': {
#                     'product':
#                     'currency':
#                     'rrp':
#                     'price':

#                 },
#                 'post_data': {

#                 },
#             },
#         ]


@registry.register_private_app
class SalesPriceGenerator(PrivateDataGenerator):
    model = SalesPrice
    count = 1
    field_mapper = {}

    def get_product_qs(self):
        return Product.objects.\
            filter_multi_tenant(self.multi_tenant_company).\
            filter_has_prices()

    def get_currency(self):
        return Currency.objects.\
            get(is_default_currency=True, multi_tenant_company=self.multi_tenant_company)

    def generate(self):
        # We override the generate function as we'll just be adding prices
        # to all existing products found.
        product_qs = self.get_product_qs()
        currency = self.get_currency()

        for product in product_qs:
            base_kwargs = {
                'multi_tenant_company': self.multi_tenant_company,
                'currency': currency,
                'product': product,
            }

            salesprice, _ = SalesPrice.objects.get_or_create(**base_kwargs)
            salesprice.rrp = fake.price()
            salesprice.price = fake.price_discount(salesprice.rrp)
            salesprice.save()


@registry.register_private_app
class SalesPriceListGenerator(PrivateStructuredDataGenerator):
    model = SalesPriceList

    def get_structure(self):
        from datetime import date

        current_year = date.today().year

        return [
            {
                'instance_data': {
                    'name': "30% Discount for Dropshippers",
                    'discount_pcnt': 30,
                    'vat_included': True,
                    'auto_update_prices': True,
                    'auto_add_products': True,
                    'currency': Currency.objects.filter(multi_tenant_company=self.multi_tenant_company).get(is_default_currency=True)
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    'name': "Summer Sales",
                    'start_date': date(current_year, 6, 1),
                    'end_date': date(current_year, 8, 31),
                    'discount_pcnt': 20,
                    'vat_included': True,
                    'auto_update_prices': True,
                    'auto_add_products': True,
                    'currency': Currency.objects.filter(multi_tenant_company=self.multi_tenant_company).get(is_default_currency=True)
                },
                'post_data': {},
            }
        ]
