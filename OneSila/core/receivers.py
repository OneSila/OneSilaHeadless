from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany

from core.schema.core.subscriptions import refresh_subscription_receiver


@receiver(post_save, sender=MultiTenantUser)
@receiver(post_save, sender=MultiTenantCompany)
def multi_tenant__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance)
