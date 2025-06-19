from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany
from core.signals import post_create, post_update
from core.schema.core.subscriptions import refresh_subscription_receiver
from sales_channels.integrations.amazon.models import AmazonSalesChannel


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


@receiver(post_save)
def core__post_create_update_triggers(sender, instance, created, **kwargs):
    """
    Let's create some new signals to handle cleaner create/update for cleaner controle.
    """
    if created:
        post_create.send(sender=instance.__class__, instance=instance)
    else:
        post_update.send(sender=instance.__class__, instance=instance)


@receiver(pre_save, sender=MultiTenantCompany)
def core__multi_tenant_company__pres_save__ensure_languages_contains_default(sender, instance, **kwargs):
    # Initialize as list if None
    if not instance.languages:
        instance.languages = []

    # Ensure the default language is present
    if instance.language and instance.language not in instance.languages:
        instance.languages.append(instance.language)


@receiver(post_save, sender=AmazonSalesChannel)
@receiver(post_delete, sender=AmazonSalesChannel)
def core__multi_tenant_company__has_amazon_integration_refresh(sender, instance, created, **kwargs):
    refresh_subscription_receiver(instance.multi_tenant_company)