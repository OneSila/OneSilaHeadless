from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Property)
@receiver(post_save, sender=PropertyTranslation)
@receiver(post_save, sender=PropertySelectValue)
@receiver(post_save, sender=ProductProperty)
def properties__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
