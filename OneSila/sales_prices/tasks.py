from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from .models import SalesPrice
from currencies.helpers import currency_convert

import logging
logger = logging.getLogger(__name__)


@db_task()
def salesprices__createupdate__task(sales_price):
    from sales_prices.flows import salesprice_updatecreate_flow
    salesprice_updatecreate_flow(sales_price)


@db_task()
def salesprice__currency_change__task(currency):
    from sales_prices.flows import salesprice_currency_change_flow
    salesprice_currency_change_flow(currency)


# @db_task()
# def salespricelistitem__update_task(sales_price_id):
#     '''
#     grab the product, find the mathing salespricelistitems and update them if the pricelist
#     has the auto_update flag
#     '''
#     from .factories import SalesPriceListItemGeneratorUpdater
#     from products.models import Product

#     product = Product.objects.get(salesprice__id=sales_price_id)
#     salespricelistitems = product.salespricelistitem_set.filter(salespricelist__auto_update=True)

#     for i in salespricelistitems:
#         fac = SalesPriceListItemGeneratorUpdater(i.salespricelist, i.product)
#         fac.run()
