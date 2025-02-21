from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from core.schema.core.subscriptions import refresh_subscription_receiver
from products.models import ProductTranslation


import logging
logger = logging.getLogger('__name__')


@receiver(post_save, sender=ProductTranslation)
def products__images__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance.product)