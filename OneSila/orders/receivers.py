from django.dispatch import receiver
from core.signals import post_create
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


@receiver(post_create, sender=Order)
def orders__order__post_save_set_customer(sender, instance, **kwargs):
    """
    When an order is saved, we must at least make sure they are marked as a customer.
    """
    instance.customer.set_is_customer()


@receiver(post_save, sender=Order)
def orders__order__status_signals_sender(sender, instance, **kwargs):
    """
    When an order gets specific status we want to send out some signals
    """
    from .signals import draft, pending_processing, pending_shipping, \
        pending_shipping_approval, to_ship, await_inventory, shipped, hold, \
        cancelled

    signals = []

    if instance.is_draft():
        signals.append(draft)
    elif instance.is_pending_processing():
        signals.append(pending_processing)
    elif instance.is_pending_shipping():
        signals.append(pending_shipping)
    elif instance.is_pending_shipping_approval():
        signals.append(pending_shipping_approval)
    elif instance.is_to_ship():
        signals.append(to_ship)
    elif instance.is_await_inventory():
        signals.append(await_inventory)
    elif instance.is_shipped():
        signals.append(shipped)
    elif instance.is_cancelled():
        signals.append(cancelled)
    elif instance.is_hold():
        signals.append(hold)

    for signal in signals:
        signal.send(sender=instance.__class__, instance=instance)
