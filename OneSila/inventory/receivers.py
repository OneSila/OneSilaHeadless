from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Inventory, InventoryLocation
from inventory.signals import inventory_sent, inventory_received

import logging
logger = logging.getLogger(__name__)


@receiver(inventory_sent, sender=InventoryLocation)
def inventories__inventory__inventory_sent(sender, instance, product, quantity_sent, **kwargs):
    instance.reduce_quantity(product, quantity_sent)


@receiver(inventory_received, sender=InventoryLocation)
def inventories__inventory__inventory_received(sender, instance, product, quantity_received, **kwargs):
    instance.increase_quantity(product, quantity_received)


@receiver(post_save, sender=Inventory)
@receiver(post_delete, sender=Inventory)
def inventories__inventory__product_trigger(sender, instance, **kwargs):
    """
    We want to send out a signal on all recursive parent products
    of the changed inventory product that inventory has been updated.

    This can be used for shipment retries, frontend updates and more.
    """
    from inventory.flows import inventory_change_product_update_trigger_flow
    inventory_change_product_update_trigger_flow(instance)
