from orders.signals import to_ship
from orders.models import Order
from core.receivers import post_save, receiver
from core.signals import post_create
from orders.signals import pending_processing
from inventory.signals import inventory_change, inventory_received
from shipments.flows import inventory_change_trigger_flow
from shipments.signals import draft, todo, in_progress, \
    done, cancelled, new, packed, dispatched
from shipments.models import Shipment, Package, PackageItem


@receiver(inventory_change, sender='products.Product')
def orders__product__inventory_change__shipping_retrigger(sender, instance, **kwargs):
    """
    Check to see if some orders need the shipping_status retriggered.
    """
    inventory_change_trigger_flow(instance)


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


@receiver(post_save, sender=Package)
def shipments__package__signals(sender, instance, **kwargs):
    signals = []

    if instance.is_new():
        signals.append(new)
    elif instance.is_in_progress():
        signals.append(in_progress)
    elif instance.is_packed():
        signals.append(packed)
    elif instance.is_dispatched():
        signals.append(dispatched)

    for signal in signals:
        signal.send(sender=instance.__class__, instance=instance)


@receiver(inventory_received, sender=Package)
def shipments__package__inventory_received(sender, instance, product, quantity_received, movement_from, **kwargs):
    from shipments.flows import packageitem_inventory_move_flow
    packageitem_inventory_move_flow(
        package=instance,
        quantity_received=quantity_received,
        movement_from=movement_from,
        product=product)


@receiver(dispatched, sender=Package)
def shipments__package__complete_shipment(sender, instance, **kwargs):
    from shipments.flows import shipment_completed_flow
    shipment_completed_flow(instance.shipment)
