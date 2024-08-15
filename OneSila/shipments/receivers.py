from orders.signals import to_ship
from orders.models import Order
from core.receivers import post_save, receiver


@receiver(to_ship, sender=Order)
def shipments__order__ship(sender, instance, **kwargs):
    """
    When an order is ready to ship, we want to prepare the shipment information
    so that the team can pick and pack.
    """
    from .tasks import prepare_shipments_task
    prepare_shipments_task(instance)
