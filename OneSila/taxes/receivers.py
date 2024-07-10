from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import MultiTenantCompany

from taxes.models import VatRate
from taxes.vat_rates import vat_rates

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=MultiTenantCompany)
def taxes__multi_tenant_company__populate_defaults(sender, instance, created, **kwargs):
    if created:
        vat_rate = vat_rates.get(instance.country, None)
        if vat_rate:
            VatRate.objects.create(rate=vat_rate, name=f'{str(vat_rate)}%', multi_tenant_company=instance)
