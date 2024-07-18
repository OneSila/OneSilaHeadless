from django.db.models.signals import post_save
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
    from .tasks import salesprices__createupdate__task
    for sales_price in instance.salesprice_set.all().iterator():
        salesprices__createupdate__task(sales_price)


@receiver(post_save, sender=SalesPriceList)
def sales_prices__salespricelist__post_save(sender, instance, **kwargs):
    # When a pricelist is updated, most likely the prices associated need an update as well.
    pass
