from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantCompany

from core.schema.core.subscriptions import refresh_subscription_receiver


@receiver(post_save)
def general__subscription__post_save(sender, instance, **kwargs):
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

@receiver(post_save, sender=MultiTenantCompany)
def core__multi_tenant_company__populate_defaults_from_multi_tenant_company(sender, instance, created, **kwargs):
    from taxes.models import VatRate
    from currencies.models import Currency
    from core.countries import vat_rates, currencies

    if created:

        vat_rate = vat_rates.get(instance.country, None)
        if vat_rate:
            VatRate.objects.create(rate=vat_rate, name=f'{str(vat_rate)}%', multi_tenant_company=instance)

        currency = currencies.get(instance.country, None)
        if currency:
            currency['is_default_currency'] = True
            currency['multi_tenant_company'] = instance
            Currency.objects.create(**currency)