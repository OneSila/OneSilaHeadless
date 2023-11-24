from django.db.models.signals import post_save
from django.dispatch import receiver
from currencies.models import Currency
from currencies.signals import exchange_rate_official__post_save
from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Currency)
def currencies__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal.
    """
    refresh_subscription_receiver(instance)


@receiver(exchange_rate_official__post_save, sender=Currency)
def currencies__currency__exchange_rate_official__receiver(sender, instance, **kwargs):
    """
    Ensure that relevant exchange rates are updates if they are blindly following.
    """
    from core.flows.update_rates import UpdateFollowerRateFlow
    UpdateFollowerRateFlow(instance).flow()
