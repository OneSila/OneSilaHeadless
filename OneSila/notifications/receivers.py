from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser
from core.signals import registered, invite_sent, \
    invite_accepted, disabled, enabled

from notifications.flows.email import send_welcome_email_flow, \
    send_user_invite_email_flow


@receiver(registered, sender=MultiTenantUser)
def notifications__email__welcome(sender, instance, **kwargs):
    send_welcome_email_flow(user=instance)


@receiver(invite_sent, sender=MultiTenantUser)
def notifications__email__invite(sender, instance, **kwargs):
    send_user_invite_email_flow(user=instance)
