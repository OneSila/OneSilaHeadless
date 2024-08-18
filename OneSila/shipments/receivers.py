from orders.signals import to_ship
from orders.models import Order
from core.receivers import post_save, receiver
from shipments.signals import draft, todo, in_progress, \
    done, cancelled


@receiver(to_ship, sender=Order)
def shipments__order__ship(sender, instance, **kwargs):
    """
    When an order is ready to ship, we want to prepare the shipment information
    so that the team can pick and pack.
    """
    from .tasks import prepare_shipments_task
    prepare_shipments_task(instance)


@receiver(post_save, sender=Shipment)
def shipments__shipment__signals(sender, instance, **kwargs):
    """
    when a shipment changes a status, we want to trigger relevant statusses
    """
    signals = []

    if instance.is_draft():
        signals.append(draft)
    elif instance.is_todo():
        signals.append(todo)
    elif instance.is_in_progress():
        signals.in_progress()
    elif instance.is_done():
        signals.append(done)
    elif instance.is_cancelled():
        signals.append(cancelled)

    for signal in signals:
        signal.send(sender=instance.__class__, instance=instance)
