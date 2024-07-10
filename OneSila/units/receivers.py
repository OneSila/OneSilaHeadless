from django.dispatch import receiver
from django.db.models.signals import post_save
from units.models import Unit

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender='core.MultiTenantCompany')
def units__multitenantcompany__post_save(sender, instance, created, **kwargs):
    if created:
        # When a new company is created, we want to create a number of default units.
        from .defaults import DEFAULT_UNITS
        for i in DEFAULT_UNITS:
            Unit.objects.get_or_create(multi_tenant_company=instance, **i)
