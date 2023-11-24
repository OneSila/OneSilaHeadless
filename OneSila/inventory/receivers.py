from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Inventory, InventoryLocation


from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Inventory)
@receiver(post_save, sender=InventoryLocation)
def inventory__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
