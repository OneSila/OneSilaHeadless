from core.signals import post_save, post_create
from django.dispatch import receiver
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from currencies.models import Currency
from currencies.signals import exchange_rate__post_save, exchange_rate_official__post_save

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=SalesPrice)
def sales_prices__salesprice__post_save(sender, instance, **kwargs):
    """
    Time to populate the prices
    """
    from .tasks import salesprices__createupdate__task
    salesprices__createupdate__task(instance)


@receiver(exchange_rate__post_save, sender=Currency)
@receiver(exchange_rate_official__post_save, sender=Currency)
def sales_prices__currencies__exchange_rate_changes(sender, instance, **kwargs):
    """
    When currencies change rates, most likely your prices need an update as well.
    """
    from .tasks import salesprice__create_for_currency__task
    salesprice__create_for_currency__task(instance)


@receiver(post_save, sender=Currency)
def sales_prices__currencies__exchange_rate_changes(sender, instance, created, **kwargs):
    """
    When currencies are added, most likely your prices need an update as well.
    """
    if created:
        from .tasks import salesprice__create_for_currency__task
        salesprice__create_for_currency__task(instance)


@receiver(post_save, sender=SalesPriceList)
def sales_prices__salespricelist__post_create(sender, instance, **kwargs):
    """When a SalesPriceList is created we may want to create all kinds of relevant SalesPriceListItems"""
    from .tasks import salespricelistitem__create_for_salespricelist__task
    salespricelistitem__create_for_salespricelist__task(instance)


@receiver(post_create, sender=SalesPrice)
def sales_prices__sales_price__post_create(sender, instance, **kwargs):
    """When a salesprice is created, you probably want to create the relevant SalesPriceListItems"""
    from .tasks import salespricelistitem__create_for_salesprice__task
    salespricelistitem__create_for_salesprice__task(instance)
