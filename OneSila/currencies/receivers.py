from core.signals import post_save, post_create
from django.dispatch import receiver
from core.models import MultiTenantCompany
from .signals import exchange_rate_change
from currencies.models import Currency

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
    from currencies.flows.default_currency import CreateDefaultCurrencyForMultiTenantCompanyFlow
    CreateDefaultCurrencyForMultiTenantCompanyFlow(instance).flow()
