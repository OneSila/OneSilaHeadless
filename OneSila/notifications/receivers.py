from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.schema.core.subscriptions.receivers import refresh_subscription_receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantUserLoginToken
from core.signals import registered, invited, \
    invite_accepted, disabled, enabled, login_token_requested, \
    recovery_token_created, password_changed, post_create

from notifications.models import CollaborationMention, Notification
from notifications.flows.email import send_welcome_email_flow, \
    send_user_invite_email_flow, send_user_login_link_email_flow, \
    send_user_account_recovery_email_flow, send_user_password_changed_email_flow


@receiver(registered, sender=MultiTenantUser)
def notifications__email__welcome(sender, instance, **kwargs):
    send_welcome_email_flow(user=instance)


@receiver(invited, sender=MultiTenantUserLoginToken)
def notifications__email__invite(sender, instance, **kwargs):
    send_user_invite_email_flow(token=instance)


@receiver(login_token_requested, sender=MultiTenantUserLoginToken)
def notifications__email__login_link(sender, instance, **kwargs):
    send_user_login_link_email_flow(token=instance)


@receiver(recovery_token_created, sender=MultiTenantUserLoginToken)
def notifications__email__recovery_link(sender, instance, **kwargs):
    send_user_account_recovery_email_flow(token=instance)


@receiver(password_changed, sender=MultiTenantUser)
def notifications__email__password_changed(sender, instance, **kwargs):
    send_user_password_changed_email_flow(user=instance)


@receiver(post_save, sender=Notification)
@receiver(post_delete, sender=Notification)
def notifications__notification__refresh_user_subscription(sender, instance, **kwargs):
    refresh_subscription_receiver(instance.user)


@receiver(post_create, sender=CollaborationMention)
def notifications__collaborationmention__create_notification(sender, instance, **kwargs):

    entry = instance.entry
    thread = entry.thread

    Notification.objects.create(
        multi_tenant_company=instance.multi_tenant_company,
        created_by_multi_tenant_user=instance.created_by_multi_tenant_user,
        last_update_by_multi_tenant_user=instance.last_update_by_multi_tenant_user,
        user=instance.user,
        type=Notification.TYPE_COLLABORATION_MENTION,
        title="Collaboration mention",
        message=entry.comment or "",
        url=thread.url,
        metadata={
            "thread_id": thread.id,
            "entry_id": entry.id,
            "mention_id": instance.id,
            "entry_type": entry.type,
        },
    )
