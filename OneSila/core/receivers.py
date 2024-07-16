from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany

from core.schema.core.subscriptions import refresh_subscription_receiver


@receiver(post_save)
def core__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    try:
        refresh_subscription_receiver(instance)
    except AttributeError:
        # We take a very greedy approach to post_save signals.
        # Since there are many post_save signals going around in Django,
        # of which many can fail if they are not models as we use them in our apps.
        # That's why we don't let AttributeErrors fail our method.
        pass
