from django.db.models.signals import post_save
from django.dispatch import receiver
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=SalesPrice)
def sales_prices__salesprice__post_save(sender, instance, **kwargs):
    """
    Time to populate the prices
    """
    from .tasks import salesprices__createupdate__task
    salesprices__createupdate__task(instance)
