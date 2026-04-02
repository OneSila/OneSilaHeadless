from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.schema.core.subscriptions.receivers import refresh_subscription_receiver
from core.models.multi_tenant import MultiTenantUser, MultiTenantUserLoginToken
from core.signals import registered, invited, \
    invite_accepted, disabled, enabled, login_token_requested, \
    recovery_token_created, password_changed, post_create, post_update

from imports_exports.models import Export, Import
from notifications.helpers import (
    build_export_url,
    build_import_tab_url,
    build_product_tab_url,
    create_user_notification,
)
from notifications.models import CollaborationMention, Notification
from notifications.flows.email import send_welcome_email_flow, \
    send_user_invite_email_flow, send_user_login_link_email_flow, \
    send_user_account_recovery_email_flow, send_user_password_changed_email_flow
from sales_channels.models import RemoteProduct, SalesChannelViewAssign


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

    create_user_notification(
        user=instance.user,
        notification_type=Notification.TYPE_COLLABORATION_MENTION,
        title="Collaboration mention",
        message=entry.comment or "",
        url=thread.url,
        actor=instance.created_by_multi_tenant_user,
        multi_tenant_company=instance.multi_tenant_company,
        metadata={
            "thread_id": thread.id,
            "entry_id": entry.id,
            "mention_id": instance.id,
            "entry_type": entry.type,
        },
    )


@receiver(post_update, sender="sales_channels.RemoteProduct")
@receiver(post_update, sender="amazon.AmazonProduct")
@receiver(post_update, sender="ebay.EbayProduct")
@receiver(post_update, sender="magento2.MagentoProduct")
@receiver(post_update, sender="mirakl.MiraklProduct")
@receiver(post_update, sender="shein.SheinProduct")
@receiver(post_update, sender="shopify.ShopifyProduct")
@receiver(post_update, sender="woocommerce.WoocommerceProduct")
def notifications__remote_product__create_status_changed_notification(sender, instance, **kwargs):
    repeat_failed_status_notification = getattr(instance, "_repeat_failed_status_notification", False)

    if not instance.local_instance_id:
        return

    if not instance.is_dirty_field("status") and not repeat_failed_status_notification:
        return

    if getattr(instance.sales_channel, "is_importing", False):
        return

    previous_status = instance.get_dirty_fields().get("status")
    if repeat_failed_status_notification and previous_status is None:
        previous_status = instance.status
    if previous_status == instance.status and not repeat_failed_status_notification:
        return

    tracked_statuses = {
        RemoteProduct.STATUS_COMPLETED,
        RemoteProduct.STATUS_FAILED,
        RemoteProduct.STATUS_PENDING_APPROVAL,
        RemoteProduct.STATUS_APPROVAL_REJECTED,
    }
    if instance.status not in tracked_statuses:
        return

    current_status_display = instance.get_status_display()
    sku = getattr(instance.local_instance, "sku", None) or instance.remote_sku or str(instance.pk)
    url = build_product_tab_url(product=instance.local_instance, tab="websites")
    assigns = (
        SalesChannelViewAssign.objects.filter(
            remote_product=instance,
            last_update_by_multi_tenant_user__isnull=False,
        )
        .select_related("last_update_by_multi_tenant_user")
        .order_by("id")
    )

    notified_user_ids: set[int] = set()
    for assign in assigns:
        user = assign.last_update_by_multi_tenant_user
        if user.id in notified_user_ids:
            continue

        create_user_notification(
            user=user,
            notification_type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED,
            title="Remote product status updated",
            message=f"Product {sku} changed to {current_status_display}.",
            url=url,
            actor=user,
            multi_tenant_company=instance.multi_tenant_company,
            metadata={
                "remote_product_id": instance.id,
                "local_product_id": instance.local_instance_id,
                "previous_status": previous_status,
                "status": instance.status,
            },
        )
        notified_user_ids.add(user.id)


@receiver(post_update, sender="imports_exports.Import")
@receiver(post_update, sender="imports_exports.TypedImport")
@receiver(post_update, sender="imports_exports.MappedImport")
@receiver(post_update, sender="sales_channels.SalesChannelImport")
@receiver(post_update, sender="amazon.AmazonSalesChannelImport")
@receiver(post_update, sender="ebay.EbaySalesChannelImport")
@receiver(post_update, sender="mirakl.MiraklSalesChannelImport")
@receiver(post_update, sender="shein.SheinSalesChannelImport")
def notifications__import__create_status_notification(sender, instance, **kwargs):
    if not instance.created_by_multi_tenant_user_id:
        return

    if not instance.is_dirty_field("status"):
        return

    previous_status = instance.get_dirty_fields().get("status")
    if previous_status == instance.status:
        return

    if instance.status not in {Import.STATUS_SUCCESS, Import.STATUS_FAILED}:
        return

    notification_type = (
        Notification.TYPE_IMPORT_FINISHED
        if instance.status == Import.STATUS_SUCCESS
        else Notification.TYPE_IMPORT_FAILED
    )
    title = "Import finished" if instance.status == Import.STATUS_SUCCESS else "Import failed"
    import_name = instance.name or instance.__class__.__name__
    current_status_display = instance.get_status_display()

    create_user_notification(
        user=instance.created_by_multi_tenant_user,
        notification_type=notification_type,
        title=title,
        message=f"{import_name} is {current_status_display}.",
        url=build_import_tab_url(import_process=instance),
        actor=instance.last_update_by_multi_tenant_user or instance.created_by_multi_tenant_user,
        multi_tenant_company=instance.multi_tenant_company,
        metadata={
            "import_id": instance.id,
            "status": instance.status,
            "previous_status": previous_status,
        },
    )


@receiver(post_update, sender="imports_exports.Export")
def notifications__export__create_status_notification(sender, instance, **kwargs):
    if not instance.created_by_multi_tenant_user_id:
        return

    if not instance.is_dirty_field("status"):
        return

    previous_status = instance.get_dirty_fields().get("status")
    if previous_status == instance.status:
        return

    if instance.status not in {Export.STATUS_SUCCESS, Export.STATUS_FAILED}:
        return

    notification_type = (
        Notification.TYPE_IMPORT_FINISHED
        if instance.status == Export.STATUS_SUCCESS
        else Notification.TYPE_IMPORT_FAILED
    )
    title = "Export finished" if instance.status == Export.STATUS_SUCCESS else "Export failed"
    export_name = instance.name or instance.__class__.__name__
    current_status_display = instance.get_status_display()

    create_user_notification(
        user=instance.created_by_multi_tenant_user,
        notification_type=notification_type,
        title=title,
        message=f"{export_name} is {current_status_display}.",
        url=build_export_url(export_process=instance),
        actor=instance.last_update_by_multi_tenant_user or instance.created_by_multi_tenant_user,
        multi_tenant_company=instance.multi_tenant_company,
        metadata={
            "export_id": instance.id,
            "status": instance.status,
            "previous_status": previous_status,
        },
    )
