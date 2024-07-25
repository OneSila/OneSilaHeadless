from django.db.models.signals import post_save
from django.dispatch import receiver
from currencies.signals import exchange_rate_change
from currencies.models import Currency
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem

import logging
logger = logging.getLogger(__name__)


@receiver(exchange_rate_change, sender=Currency)
def salesprices__salesprice_change_on_currency_rate_change(sender, instance, **kwargs):
    from .tasks import salesprice__currency_change__task
    salesprice__currency_change__task(instance)


@receiver(exchange_rate_change, sender=SalesPrice)
@receiver(post_save, sender=SalesPrice)
def sales_prices__salesprice__post_save(sender, instance, **kwargs):
    """
    Time to populate the prices
    """
    from .tasks import salesprices__createupdate__task
    salesprices__createupdate__task(instance)
