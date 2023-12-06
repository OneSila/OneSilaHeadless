from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantUserLoginToken
from core.signals import registered, invite_sent, \
    invite_accepted, disabled, enabled, login_token_created, \
    recovery_token_created

from notifications.flows.email import send_welcome_email_flow, \
    send_user_invite_email_flow, send_user_login_link_email_flow, \
    send_user_account_recovery_email_flow


@receiver(registered, sender=MultiTenantUser)
def notifications__email__welcome(sender, instance, **kwargs):
    send_welcome_email_flow(user=instance)


@receiver(invite_sent, sender=MultiTenantUser)
def notifications__email__invite(sender, instance, **kwargs):
    send_user_invite_email_flow(user=instance)


@receiver(login_token_created, sender=MultiTenantUserLoginToken)
def notifications__email__login_link(sender, instance, **kwargs):
    send_user_login_link_email_flow(token=instance)


@receiver(recovery_token_created, sender=MultiTenantUserLoginToken)
def notifications__email__recovery_link(sender, instance, **kwargs):
    send_user_account_recovery_email_flow(token=instance)
