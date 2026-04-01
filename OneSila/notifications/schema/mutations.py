import strawberry_django
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from strawberry import Info

from core.models import MultiTenantUser
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_current_user, get_multi_tenant_company
from core.schema.core.mutations import type
from core.schema.core.subscriptions.receivers import refresh_subscription_receiver
from notifications.models import Notification, CollaborationEntry, CollaborationMention

from .helpers import get_or_create_collaboration_thread
from .types.input import OpenNotificationInput, CreateCollaborationEntryInput
from .types.types import NotificationType, CollaborationEntryType


@type(name="Mutation")
class NotificationsMutation:
    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def open_notification(self, info: Info, *, data: OpenNotificationInput) -> NotificationType:
        user = get_current_user(info)
        if data.id.type_name != "NotificationType":
            raise PermissionDenied("Invalid notification")

        notification = Notification.objects.get(
            id=data.id.node_id,
            multi_tenant_company=user.multi_tenant_company,
        )

        if notification.user_id != user.id:
            raise PermissionDenied("Invalid notification")

        notification.opened = True
        notification.last_update_by_multi_tenant_user = user
        notification.save()
        return notification

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def mark_notification_as_unread(self, info: Info, *, data: OpenNotificationInput) -> NotificationType:
        user = get_current_user(info)
        if data.id.type_name != "NotificationType":
            raise PermissionDenied("Invalid notification")

        notification = Notification.objects.get(
            id=data.id.node_id,
            multi_tenant_company=user.multi_tenant_company,
        )

        if notification.user_id != user.id:
            raise PermissionDenied("Invalid notification")

        notification.opened = False
        notification.last_update_by_multi_tenant_user = user
        notification.save()
        return notification

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def mark_all_notifications_as_view(self, info: Info) -> bool:
        user = get_current_user(info)
        Notification.objects.filter(
            multi_tenant_company=user.multi_tenant_company,
            user=user,
            opened=False,
        ).update(
            opened=True,
            updated_at=timezone.now(),
            last_update_by_multi_tenant_user=user,
        )
        refresh_subscription_receiver(user)
        return True

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def create_collaboration_entry(
        self,
        info: Info,
        *,
        data: CreateCollaborationEntryInput,
    ) -> CollaborationEntryType:
        current_user = get_current_user(info)
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        valid_types = {choice for choice, _ in CollaborationEntry.TYPE_CHOICES}
        if data.type not in valid_types:
            raise ValidationError({"type": "Invalid collaboration entry type."})

        if data.type == CollaborationEntry.TYPE_COMMENT and not (data.comment or "").strip():
            raise ValidationError({"comment": "Comment is required for COMMENT entries."})

        with transaction.atomic():
            thread, _ = get_or_create_collaboration_thread(
                info=info,
                target_id=data.target_id,
                url=data.url,
            )

            entry = CollaborationEntry.objects.create(
                multi_tenant_company=multi_tenant_company,
                created_by_multi_tenant_user=current_user,
                last_update_by_multi_tenant_user=current_user,
                thread=thread,
                type=data.type,
                comment=data.comment,
                metadata=data.metadata or {},
            )

            mention_global_ids = data.mentioned_user_ids or []
            invalid_user_type_ids = [
                str(global_id)
                for global_id in mention_global_ids
                if global_id.type_name not in {"MultiTenantUserType", "MinimalMultiTenantUserType"}
            ]
            if invalid_user_type_ids:
                raise ValidationError({"mentionedUserIds": "Invalid mentioned users."})

            mention_ids = list(
                dict.fromkeys(int(global_id.node_id) for global_id in mention_global_ids)
            )
            if mention_ids:
                mentioned_users = list(
                    MultiTenantUser.objects.filter(
                        id__in=mention_ids,
                        multi_tenant_company=multi_tenant_company,
                    )
                )
                found_ids = {user.id for user in mentioned_users}
                missing_ids = [user_id for user_id in mention_ids if user_id not in found_ids]
                if missing_ids:
                    raise ValidationError({"mentionedUserIds": "Invalid mentioned users."})

                for mentioned_user in mentioned_users:
                    CollaborationMention.objects.create(
                        multi_tenant_company=multi_tenant_company,
                        created_by_multi_tenant_user=current_user,
                        last_update_by_multi_tenant_user=current_user,
                        entry=entry,
                        user=mentioned_user,
                    )

        return CollaborationEntry.objects.select_related(
            "thread",
            "created_by_multi_tenant_user",
        ).prefetch_related("mentions__user").get(pk=entry.pk)
