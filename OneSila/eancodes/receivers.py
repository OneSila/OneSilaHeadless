from django.db.models.signals import post_save
from django.dispatch import receiver
from eancodes.models import EanCode

from core.schema.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=EanCode)
def eancodes__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
