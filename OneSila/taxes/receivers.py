from django.db.models.signals import post_save
from django.dispatch import receiver
from core.countries import vat_rates
from core.models import MultiTenantCompany
from taxes.models import VatRate

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=MultiTenantCompany)
def vat_rates__populate_from_multi_tenant_company(sender, instance, created, **kwargs):
    if created:
        vat_rate = vat_rates.get(instance.country, None)
        if vat_rate:
            VatRate.objects.create(rate=vat_rate, name=f'{str(vat_rate)}%', multi_tenant_company=instance)

@receiver(post_save, sender=VatRate)
def vat_rates__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
