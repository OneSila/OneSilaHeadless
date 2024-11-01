from django.db.models.signals import post_save

from accounting.integrations.quickbooks.models import QuickbooksAccount
from core.receivers import receiver
from core.signals import post_create

@receiver(post_create, sender=QuickbooksAccount)
def quickbooks__account__create__auth(sender, instance, **kwargs):
    from accounting.integrations.quickbooks.factories.account import QuickbooksAccountAuthorizationFactory
    from accounting.integrations.quickbooks.factories import QuickbooksVatPullFactory

    fac = QuickbooksAccountAuthorizationFactory(instance)
    fac.run()


    vat_fac = QuickbooksVatPullFactory(instance)
    vat_fac.run()