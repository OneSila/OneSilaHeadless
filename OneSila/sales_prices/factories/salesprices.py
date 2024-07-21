from sales_prices.models import SalesPrice
from currencies.helpers import currency_convert
from products.models import Product

import logging
logger = logging.getLogger(__name__)


class SalesPriceCreateForCurrencyFactory:
    """
    This factory has 1 job: create Salesprices when a new currency is introduced.
    The prices get populated later on by another flow.
    """

    def __init__(self, currency):
        self.multi_tenant_company = currency.multi_tenant_company
        self.currency = currency

    def set_product_qs(self):
        self.product_qs = Product.objects.filter_multi_tenant(self.multi_tenant_company)

    def create_salesprices(self):
        for prod in self.product_qs.iterator():
            prod.salesprice_set.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                currency=self.currency
            )

    def run(self):
        self.set_product_qs()
        self.create_salesprices()


class SalesPriceUpdateCreateFactory:
    def __init__(self, sales_price):
        self.sales_price = sales_price
        self.product = sales_price.product
        self.multi_tenant_company = sales_price.multi_tenant_company

    def _set_inheriting_currencies(self):
        self.inheriting_currencies = self.sales_price.currency.passes_to.all()

    def _cycle_through_currencies(self):
        for currency in self.inheriting_currencies:
            self._update_create_salesprice(currency)

    def get_exchange_rate(self, currency):
        if currency.follow_official_rate:
            return currency.exchange_rate_official

        return currency.exchange_rate

    def _update_create_salesprice(self, currency):
        rrp = currency_convert(
            round_prices_up_to=currency.round_prices_up_to,
            exchange_rate=self.get_exchange_rate(currency),
            price=self.sales_price.parent_aware_rrp
        )

        price = currency_convert(
            round_prices_up_to=currency.round_prices_up_to,
            exchange_rate=self.get_exchange_rate(currency),
            price=self.sales_price.parent_aware_price
        )

        child_sales_price, _ = SalesPrice.objects.get_or_create(
            product=self.product,
            currency=currency,
            multi_tenant_company=self.multi_tenant_company)

        child_sales_price.rrp = rrp
        child_sales_price.price = price
        child_sales_price.save()

    def _update_self(self):
        # If you're part of an inhertiance, update yourself:
        if self.sales_price.currency.inherits_from:
            currency = self.sales_price.currency

            rrp = currency_convert(
                round_prices_up_to=currency.round_prices_up_to,
                exchange_rate=currency.exchange_rate,
                price=self.sales_price.parent_aware_rrp
            )

            if self.sales_price.parent_aware_price:
                price = currency_convert(
                    round_prices_up_to=currency.round_prices_up_to,
                    exchange_rate=currency.exchange_rate,
                    price=self.sales_price.parent_aware_price
                )
            else:
                price = None

            # There seems to be an issue trying to save below the .save() way.
            # Workarround by updating the queryset.  This doesn't trigger any
            # signals - which is great - since it avoids needing to deal with
            # upating 'self' and ending up in a loop.
            sales_price_queryset = SalesPrice.objects.filter(id=self.sales_price.id)
            sales_price_queryset.update(rrp=rrp, price=price)

    def run(self):
        self._set_inheriting_currencies()
        self._update_self()
        self._cycle_through_currencies()
