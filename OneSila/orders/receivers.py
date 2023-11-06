from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from orders.models import Order, OrderItem, OrderNote


from core.schema.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
@receiver(post_save, sender=OrderItem)
@receiver(post_save, sender=OrderNote)
def orders__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)


@receiver(pre_save, sender=OrderItem)
def orders__order_item__pre_save(sender, instance, **kwargs):
    '''
    set a price if there is none supplied
    '''
    from .factories import OrderItemPriceSetFactory
    fac = OrderItemPriceSetFactory(instance)
    fac.run()
