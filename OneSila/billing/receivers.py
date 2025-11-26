from django.dispatch import receiver
from billing.models import AiPointTransaction
from core.signals import post_create


@receiver(post_create, sender=AiPointTransaction)
def billing__update_multi_tenant_company_ai_points(sender, instance, **kwargs):

    company = instance.multi_tenant_company
    if instance.transaction_type == AiPointTransaction.SUBTRACT:
        company.ai_points -= instance.points
    else:
        company.ai_points += instance.points

    company.save(update_fields=['ai_points'])
