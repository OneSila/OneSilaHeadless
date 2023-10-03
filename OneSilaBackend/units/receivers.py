from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from .models import Unit


@receiver(post_save, sender='django_shared_multi_tenant.MultiTenantCompany')
def django_shared_multi_tenant__mutlitenantcompany__post_save(sender, instance, created, **kwargs):
    if created:
        # When a new company is created, we want to craete a number of default units.
        from .defaults import DEFAULT_UNITS
        for i in DEFAULT_UNITS:
            Unit.objects.get_or_create(multi_tenant_company=instance, **i)
