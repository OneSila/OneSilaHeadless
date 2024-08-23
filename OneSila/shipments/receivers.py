from orders.signals import to_ship
from orders.models import Order
from core.receivers import post_save, receiver
from inventory.signals import product_inventory_change
from shipments.signals import draft, todo, in_progress, \
    done, cancelled, pending_processing


@receiver(product_inventory_change, sender='products.Product')
def orders__product__inventory_change__shipping_retrigger(sender, instance, **kwargs):
    """
    Check to see if some orders need the shipping_status retriggered.
    """
    # FIXME: Trace back all order_items owned by this product filtered
    # by an order that's in pending_inventory.
    # You can simply run the pre-approval flow on this one.
    pass


@receiver(pending_processing, sender=Order)
def shipments__order__ship_pre_approval(sender, instance, **kwargs):
    """
    When an order is ready for shipping, check if it has all
    inventory present and mark for approval when required.
    """
    from .tasks import pre_approve_shipping_task
    pre_approve_shipping_task(instance)


@receiver(to_ship, sender=Order)
def shipments__order__ship(sender, instance, **kwargs):
    """
    When an order is ready to ship, we want to prepare the shipment information
    so that the team can pick and pack.
    """
    from .tasks import prepare_shipments_task
    prepare_shipments_task(instance)


@receiver(done, sender=Shipment)
def shipments__shipment__done(sender, instance, **kwargs):
    """When a shipment is done, we want to remove the inventory"""
    from .tasks import remove_inventory_after_shipping_task
    remove_inventory_after_shipping_task(instance)


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
