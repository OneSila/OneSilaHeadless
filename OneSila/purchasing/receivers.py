from core.receivers import receiver
from core.signals import post_save
from orders.signals import pending_processing
from purchasing.models import PurchaseOrder

import logging
logger = logging.getLogger(__name__)


@receiver(pending_processing, sender='orders.Order')
def purchasing__order__buy_dropshippingproducts(sender, instance, **kwargs):
    from purchasing.tasks import buy_dropshippingproducts_task
    buy_dropshippingproducts_task(instance)


@receiver(post_save, sender=PurchaseOrder)
def purchasing__purchaseorder__status_signals_sender(sender, instance, **kwargs):
    """
    When an order gets specific status we want to send out some signals
    """
    from .signals import draft, to_order, ordered, confirmed, pending_delivery, \
        delivered

    signals = []

    if instance.is_draft():
        signals.append(draft)
    elif instance.is_to_order():
        signals.append(to_order)
    elif instance.is_confirmed():
        signals.append(confirmed)
    elif instance.is_pending_delivery():
        signals.append(pending_delivery)
    elif instance.is_delivered():
        signals.append(is_delivered)

    for signal in signals:
        signal.send(sender=instance.__class__, instance=instance)
