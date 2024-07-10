from sales_prices.models import SalesPrice
from currencies.helpers import currency_convert

import logging
logger = logging.getLogger(__name__)


class SalesPriceUpdateCreateFactory:
    def __init__(self, sales_price):
        self.sales_price = sales_price
        self.product = sales_price.product
        self.multi_tenant_company = sales_price.multi_tenant_company

    def _set_inheriting_currencies(self):
        self.inheriting_currencies = self.sales_price.currency.passes_to.all()

        logger.debug(f"Discovered {self.inheriting_currencies.count()} currencies to populate")

    def _cycle_through_currencies(self):
        for currency in self.inheriting_currencies:
            self._update_create_salesprice(currency)

    def get_exchange_rate(self, currency):
        if currency.follow_official_rate:
            return currency.exchange_rate_official

        return currency.exchange_rate

    def _update_create_salesprice(self, currency):
        amount = currency_convert(
            round_prices_up_to=currency.round_prices_up_to,
            exchange_rate=self.get_exchange_rate(currency),
            price=self.sales_price.parent_aware_amount
        )

        if self.sales_price.parent_aware_discount_amount:
            discount_amount = currency_convert(
                round_prices_up_to=currency.round_prices_up_to,
                exchange_rate=self.get_exchange_rate(currency),
                price=self.sales_price.parent_aware_discount_amount
            )
        else:
            discount_amount = None

        try:
            child_sales_price = currency.salesprice_set.get(product=self.product)
            child_sales_price.amount = amount
            child_sales_price.discount_amount = discount_amount
            child_sales_price.save()
        except SalesPrice.DoesNotExist:
            child_sales_price = SalesPrice.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                currency=currency,
                amount=amount)

    def _update_self(self):
        # If you're part of an inhertiance, update yourself:
        if self.sales_price.currency.inherits_from:
            currency = self.sales_price.currency

            amount = currency_convert(
                round_prices_up_to=currency.round_prices_up_to,
                exchange_rate=currency.exchange_rate,
                price=self.sales_price.parent_aware_amount
            )

            if self.sales_price.parent_aware_discount_amount:
                discount_amount = currency_convert(
                    round_prices_up_to=currency.round_prices_up_to,
                    exchange_rate=currency.exchange_rate,
                    price=self.sales_price.parent_aware_discount_amount
                )
            else:
                discount_amount = None

            # There seems to be an issue trying to save below the .save() way.
            # Workarround by updating the queryset.  This doesn't trigger any
            # signals - which is great - since it avoids needing to deal with
            # upating 'self' and ending up in a loop.
            sales_price_queryset = SalesPrice.objects.filter(id=self.sales_price.id)
            sales_price_queryset.update(amount=amount, discount_amount=discount_amount)

    def run(self):
        self._set_inheriting_currencies()
        self._update_self()
        self._cycle_through_currencies()


# @db_task()
# def sales_price_update_create_task(sales_price_id):
#     # @TODO: Move this in a flow.
#     '''
#     Acts as task to create the necessary child-prices or force updates on child prices.
#     if the price acts as a maaster-price there is no need for updates.
#     '''
#     sales_price = SalesPrice.objects.get(id=sales_price_id)
#     product = sales_price.product

#     # force updates on all children throug its currencies.
#     inheritance = sales_price.currency.passes_to.all()
#     for currency in inheritance:

#         # amount = currency_convert(
#         #     round_prices_up_to=currency.round_prices_up_to,
#         #     exchange_rate=currency.exchange_rate,
#         #     price=sales_price.parent_aware_amount
#         # )

#         # if sales_price.parent_aware_discount_amount:
#         #     discount_amount = currency_convert(
#         #         round_prices_up_to=currency.round_prices_up_to,
#         #         exchange_rate=currency.exchange_rate,
#         #         price=sales_price.parent_aware_discount_amount
#         #     )
#         # else:
#         #     discount_amount = None

#         # try:
#         #     child_sales_price = currency.salesprice_set.get(product=product)
#         #     child_sales_price.amount = amount
#         #     child_sales_price.discount_amount = discount_amount
#         #     child_sales_price.save()
#         # except SalesPrice.DoesNotExist:
#         #     child_sales_price = SalesPrice.objects.create(
#         #         product=product,
#         #         currency=currency,
#         #         amount=amount)

#     # If you're part of an inhertiance, update yourself:
#     if sales_price.currency.inherits_from:
#         currency = sales_price.currency

#         amount = currency_convert(
#             round_prices_up_to=currency.round_prices_up_to,
#             exchange_rate=currency.exchange_rate,
#             price=sales_price.parent_aware_amount
#         )

#         if sales_price.parent_aware_discount_amount:
#             discount_amount = currency_convert(
#                 round_prices_up_to=currency.round_prices_up_to,
#                 exchange_rate=currency.exchange_rate,
#                 price=sales_price.parent_aware_discount_amount
#             )
#         else:
#             discount_amount = None

#         # There seems to be an issue trying to save below the .save() way.
#         # Workarround by updating the queryset.  This doesn't trigger any
#         # signals - which is great - since it avoids needing to deal with
#         # upating 'self' and ending up in a loop.
#         sales_price_queryset = SalesPrice.objects.filter(id=sales_price_id)
#         sales_price_queryset.update(amount=amount, discount_amount=discount_amount)

#     return True
