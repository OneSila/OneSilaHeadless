from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from orders.models import Order, OrderItem, OrderNote


import logging
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=OrderItem)
def orders__order_item__pre_save(sender, instance, **kwargs):
    '''
    set a price if there is none supplied
    '''
    # @TODO: FIX THIS! WAS IMPORTING A NON EXISTING FACTORY!
    # from .factories import OrderItemPriceSetFactory
    # fac = OrderItemPriceSetFactory(instance)
    # fac.run()
    pass


@receiver(post_save, sender=Order)
def orders__order__post_save_set_customer(sender, instance, **kwargs):
    """
    When an order is saved, we must at least make sure they are marked as a customer.
    """
    instance.customer.set_is_customer()
