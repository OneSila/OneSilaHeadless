from core.signals import post_save, post_create
from django.dispatch import receiver
from core.models import MultiTenantCompany
from currencies.models import Currency
from currencies.signals import exchange_rate_official__post_save

import logging
logger = logging.getLogger(__name__)


@receiver(post_create, sender=Currency)
def currencies__currency__post_create(sender, instance, **kwargs):
    """
    When a currency is created, we want to populate the rates immediately.
    """
    from currencies.flows.update_rates import update_single_rate_flow
    update_single_rate_flow(instance)


@receiver(post_create, sender=MultiTenantCompany)
def currencies__multi_tenant_company__populate_defaults(sender, instance, **kwargs):
    from currencies.currencies import currencies

    currency = currencies.get(instance.country, None)
    if currency:
        currency['is_default_currency'] = True
        currency['multi_tenant_company'] = instance
        Currency.objects.create(**currency)
