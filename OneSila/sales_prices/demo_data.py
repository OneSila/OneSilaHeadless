from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from currencies.models import Currency
from products.models import Product
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from datetime import datetime

registry = DemoDataLibrary()


@registry.register_private_app
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
            salesprice.rrp = fake.price()
            salesprice.price = fake.price_discount(salesprice.rrp)
            salesprice.save()


@registry.register_private_app
class SalesPriceListGenerator(PrivateDataGenerator):
    model = SalesPriceList
    count = 20

    field_mapper = {
        'name': lambda: fake.date_between_dates(date_start=datetime(2024, 1, 1), date_end=datetime(2030, 12, 31)).strftime("%B %Y"),
        'discount': lambda: round(fake.random_number(digits=2) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2),
        'notes': fake.text,
        'vat_included': lambda: fake.boolean(),
        'auto_update_prices': lambda: fake.boolean()
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        currency = Currency.objects.filter(multi_tenant_company=multi_tenant_company).order_by('?').first()
        kwargs['currency'] = currency

        return kwargs


@registry.register_private_app
class SalesPriceListItemGenerator(PrivateDataGenerator):
    model = SalesPriceListItem
    count = 200

    field_mapper = {
        'salesprice': lambda: round(fake.random_number(digits=3) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']

        salespricelist = SalesPriceList.objects.filter(multi_tenant_company=multi_tenant_company).order_by('?').first()
        existing_product_ids = SalesPriceListItem.objects.filter(salespricelist=salespricelist, multi_tenant_company=multi_tenant_company).values_list(
            'product_id', flat=True)

        product = Product.objects.filter(multi_tenant_company=multi_tenant_company).exclude(id__in=existing_product_ids).order_by('?').first()
        kwargs['product'] = product
        kwargs['salespricelist'] = salespricelist

        return kwargs
