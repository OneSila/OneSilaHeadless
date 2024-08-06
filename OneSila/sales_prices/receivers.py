from core.signals import post_save, post_create
from django.dispatch import receiver
from currencies.signals import exchange_rate_change
from currencies.models import Currency
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from currencies.models import Currency

import logging
logger = logging.getLogger(__name__)


@receiver(exchange_rate_change, sender=SalesPrice)
@receiver(post_save, sender=SalesPrice)
def sales_prices__salesprice__post_save(sender, instance, created=False, **kwargs):
    """
    Time to populate the prices
    """
    from .tasks import salesprices__createupdate__task, \
        sales_price__salespricelistitem__update_prices_task, \
        salespricelistitem__create_for_salesprice__task

    if created:
        # When a salesprice is created, you probably want to create the relevant SalesPriceListItems
        salespricelistitem__create_for_salesprice__task(instance)

    # When a salesprice has been saved, child prices may need updating.
    salesprices__createupdate__task(instance)

    # When a salesprice has been saved, the relavant salespriceitems may need updating
    sales_price__salespricelistitem__update_prices_task(instance)


@receiver(post_create, sender=Currency)
def sales_prices__currencies__exchange_rate_changes(sender, instance, **kwargs):
    """
    When currencies change rates, most likely your prices need an update as well.
    """
    from .tasks import salesprice__create_for_currency__task
    salesprice__create_for_currency__task(instance)


@receiver(exchange_rate_change, sender=Currency)
def salesprices__salesprice_change_on_currency_rate_change(sender, instance, **kwargs):
    """
    When exchange rates change, we want to ensure that the right salesprices get
    an update trigger
    """
    from .tasks import salesprice__currency_change__task
    salesprice__currency_change__task(instance)


@receiver(post_save, sender=SalesPriceList)
def sales_prices__salespricelist__post_create(sender, instance, created, **kwargs):
    from .tasks import salespricelistitem__create_for_salespricelist__task, \
        sales_price_list__salespricelistitem__update_prices_task

    if created:
        # When a SalesPriceList is created we may want to create all kinds of relevant SalesPriceListItems
        salespricelistitem__create_for_salespricelist__task(instance)

    # When a price list is saved, we may need to update the relevant salespriceitems
    sales_price_list__salespricelistitem__update_prices_task(instance)


@receiver(post_create, sender=SalesPriceListItem)
def salespricelistitem__salespricelist__post_create(sender, instance, **kwargs):
    from .tasks import salespricelistitem__update_prices_task

    # When a salespricelist item has been created, we need to update the prices for it.
    # This manual route is needed for when a product is added to a price list where products
    # are added manually
    salespricelistitem__update_prices_task(instance)
