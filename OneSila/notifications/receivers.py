from django.dispatch import receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantUserLoginToken
from core.signals import registered, invited, \
    invite_accepted, disabled, enabled, login_token_created, \
    recovery_token_created, password_changed

from notifications.flows.email import send_welcome_email_flow, \
    send_user_invite_email_flow, send_user_login_link_email_flow, \
    send_user_account_recovery_email_flow, send_user_password_changed_email_flow


@receiver(registered, sender=MultiTenantUser)
def notifications__email__welcome(sender, instance, **kwargs):
    send_welcome_email_flow(user=instance)


@receiver(invited, sender=MultiTenantUserLoginToken)
def notifications__email__invite(sender, instance, **kwargs):
    send_user_invite_email_flow(token=instance)


@receiver(login_token_created, sender=MultiTenantUserLoginToken)
def notifications__email__login_link(sender, instance, **kwargs):
    send_user_login_link_email_flow(token=instance)


@receiver(recovery_token_created, sender=MultiTenantUserLoginToken)
def notifications__email__recovery_link(sender, instance, **kwargs):
    send_user_account_recovery_email_flow(token=instance)


@receiver(password_changed, sender=MultiTenantUser)
def notifications__email__password_changed(sender, instance, **kwargs):
    send_user_password_changed_email_flow(user=instance)
