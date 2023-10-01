from django.db.models.signals import post_save
from django.dispatch import receiver
from contacts.models import Company
from core.schema.subscriptions import refresh_subscription

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Company)
def send_company_message(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription(instance)
