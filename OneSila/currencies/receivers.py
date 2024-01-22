from django.db.models.signals import post_save
from django.dispatch import receiver
from currencies.models import Currency
from currencies.signals import exchange_rate_official__post_save

import logging
logger = logging.getLogger(__name__)


@receiver(exchange_rate_official__post_save, sender=Currency)
def currencies__currency__exchange_rate_official__receiver(sender, instance, **kwargs):
    """
    Ensure that relevant exchange rates are updates if they are blindly following.
    """
    from currencies.flows.update_rates import UpdateFollowerRateFlow
    UpdateFollowerRateFlow(instance).flow()
