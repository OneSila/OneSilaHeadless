from django.db.models.signals import post_save
from django.dispatch import receiver
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=SalesPrice)
@receiver(post_save, sender=SalesPriceList)
@receiver(post_save, sender=SalesPriceListItem)
def sales_prices__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
