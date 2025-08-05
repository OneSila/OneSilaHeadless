from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from datetime import date, timedelta
from core.decorators import run_task_after_commit

import logging

from .signals import price_changed

logger = logging.getLogger(__name__)


# @run_task_after_commit
@db_task()
def salesprices__createupdate__task(sales_price):
    from sales_prices.flows import salesprice_updatecreate_flow
    salesprice_updatecreate_flow(sales_price)


# @run_task_after_commit
@db_task()
def salesprice__currency_change__task(currency):
    from sales_prices.flows import salesprice_currency_change_flow
    salesprice_currency_change_flow(currency)


# @run_task_after_commit
@db_task()
def salesprice__create_for_currency__task(currency):
    from sales_prices.flows import salesprice_create_for_currency_flow
    salesprice_create_for_currency_flow(currency)


# @run_task_after_commit
@db_task()
def salespricelistitem__create_for_salespricelist__task(salespricelist):
    from sales_prices.flows import sales_price_list__salespricelistitem__create_update_flow
    sales_price_list__salespricelistitem__create_update_flow(salespricelist)


# @run_task_after_commit
@db_task()
def salespricelistitem__create_for_salesprice__task(sales_price):
    from sales_prices.flows import sales_price__salespricelistitem__create_update_flow
    sales_price__salespricelistitem__create_update_flow(sales_price)


# @run_task_after_commit
@db_task()
def sales_price__salespricelistitem__update_prices_task(sales_price):
    from sales_prices.flows import sales_price__salespricelistitem__update_prices_flow
    sales_price__salespricelistitem__update_prices_flow(sales_price)


# @run_task_after_commit
@db_task()
def sales_price_list__salespricelistitem__update_prices_task(salespricelist):
    from sales_prices.flows import sales_price_list__salespricelistitem__update_prices_flow
    sales_price_list__salespricelistitem__update_prices_flow(salespricelist)


# @run_task_after_commit
@db_task()
def salespricelistitem__update_prices_task(salespricelistitem):
    from sales_prices.flows import salespricelistitem__update_prices_flow
    salespricelistitem__update_prices_flow(salespricelistitem)


@db_periodic_task(crontab(hour=2, minute=0))
def salespricelistitem__check_price_changed_periodic_task():
    from .models import SalesPriceList
    """
    Periodic task to check for promotions starting or ending.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    ending_promotions = SalesPriceList.objects.filter(end_date=yesterday)
    for salespricelist in ending_promotions:
        for item in salespricelist.salespricelistitem_set.all().iterator():
            price_changed.send(sender=item.product.__class__, instance=item.product, currency=salespricelist.currency)

    starting_promotions = SalesPriceList.objects.filter(start_date=today)
    for salespricelist in starting_promotions:
        for item in salespricelist.salespricelistitem_set.all().iterator():
            price_changed.send(sender=item.product.__class__, instance=item.product, currency=salespricelist.currency)
