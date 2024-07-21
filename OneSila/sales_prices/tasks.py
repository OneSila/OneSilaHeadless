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
def salesprice__create_for_currency__task(currency):
    from sales_prices.flows import salesprice_create_for_currency_flow
    salesprice_create_for_currency_flow(currency)


@db_task()
def salespricelistitem__create_for_salespricelist__task(salespricelist):
    from sales_prices.flows import sales_price_list__salespricelistitem__create_update_flow
    sales_price_list__salespricelistitem__create_update_flow(salespricelist)


@db_task()
def salespricelistitem__create_for_salesprice__task(sales_price):
    from sales_prices.flows import salespricelistitem_create_flow
    sales_price__salespricelistitem__create_flow(sales_price)
