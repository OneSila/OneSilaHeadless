from defaults.helpers import exists

from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from .models import SalesPrice
from currencies.helpers import currency_convert

import logging
logger = logging.getLogger(__name__)


@db_task()
def salespricelistitem__update_task(sales_price_id):
    '''
    grab the product, find the mathing salespricelistitems and update them if the pricelist
    has the auto_update flag
    '''
    from .factories import SalesPriceListItemGeneratorUpdater
    from products.models import Product

    product = Product.objects.get(salesprice__id=sales_price_id)
    salespricelistitems = product.salespricelistitem_set.filter(salespricelist__auto_update=True)

    for i in salespricelistitems:
        fac = SalesPriceListItemGeneratorUpdater(i.salespricelist, i.product)
        fac.run()


@db_task()
def sales_price_update_create_task(sales_price_id):
    '''
    Acts as task to create the necessary child-prices or force updates on child prices.
    if the price acts as a maaster-price there is no need for updates.
    '''
    sales_price = SalesPrice.objects.get(id=sales_price_id)
    product = sales_price.product

    # force updates on all children throug its currencies.
    inheritance = sales_price.currency.passes_to.all()
    for currency in inheritance:

        amount = currency_convert(
            round_prices_up_to=currency.round_prices_up_to,
            exchange_rate=currency.exchange_rate,
            price=sales_price.parent_aware_amount
        )

        if sales_price.parent_aware_discount_amount:
            discount_amount = currency_convert(
                round_prices_up_to=currency.round_prices_up_to,
                exchange_rate=currency.exchange_rate,
                price=sales_price.parent_aware_discount_amount
            )
        else:
            discount_amount = None

        try:
            child_sales_price = currency.salesprice_set.get(product=product)
            child_sales_price.amount = amount
            child_sales_price.discount_amount = discount_amount
            child_sales_price.save()
        except SalesPrice.DoesNotExist:
            child_sales_price = SalesPrice.objects.create(
                product=product,
                currency=currency,
                amount=amount)

    # If you're part of an inhertiance, update yourself:
    if exists(sales_price.currency.inherits_from):
        currency = sales_price.currency

        amount = currency_convert(
            round_prices_up_to=currency.round_prices_up_to,
            exchange_rate=currency.exchange_rate,
            price=sales_price.parent_aware_amount
        )

        if sales_price.parent_aware_discount_amount:
            discount_amount = currency_convert(
                round_prices_up_to=currency.round_prices_up_to,
                exchange_rate=currency.exchange_rate,
                price=sales_price.parent_aware_discount_amount
            )
        else:
            discount_amount = None

        # There seems to be an issue trying to save below the .save() way.
        # Workarround by updating the queryset.  This doesn't trigger any
        # signals - which is great - since it avoids needing to deal with
        # upating 'self' and ending up in a loop.
        sales_price_queryset = SalesPrice.objects.filter(id=sales_price_id)
        sales_price_queryset.update(amount=amount, discount_amount=discount_amount)

    return True
