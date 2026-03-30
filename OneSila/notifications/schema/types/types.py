from typing import TYPE_CHECKING

from core.schema.core.types.types import relay, type, field, lazy, Annotated
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from notifications.models import (
    Notification,
    CollaborationThread,
    CollaborationEntry,
    CollaborationMention,
)

if TYPE_CHECKING:
    from core.schema.multi_tenant.types.types import MultiTenantUserType


@type(
    Notification,
    pagination=True,
    fields=["id", "type", "title", "message", "url", "opened", "metadata", "created_at", "updated_at"],
)
class NotificationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(
    CollaborationThread,
    fields=["id", "url", "created_at", "updated_at"],
)
class CollaborationThreadType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def target_id(self, info) -> str | None:
        target = self.content_object
        if target is None:
            return None

        return getattr(target, "global_id", None)

    @field()
    def entries(self, info) -> list[Annotated["CollaborationEntryType", lazy("notifications.schema.types.types")]]:
        return CollaborationEntry.objects.filter(thread=self).select_related(
            "thread",
            "created_by_multi_tenant_user",
        ).prefetch_related("mentions__user").order_by("created_at", "id")


@type(
    CollaborationEntry,
    fields=["id", "thread", "type", "comment", "metadata", "created_at", "updated_at", "created_by_multi_tenant_user"],
)
class CollaborationEntryType(relay.Node, GetQuerysetMultiTenantMixin):
    thread: Annotated["CollaborationThreadType", lazy("notifications.schema.types.types")]
    created_by_multi_tenant_user: Annotated["MultiTenantUserType", lazy("core.schema.multi_tenant.types.types")] | None

    @field()
    def mentions(self, info) -> list[Annotated["CollaborationMentionType", lazy("notifications.schema.types.types")]]:
        return CollaborationMention.objects.filter(entry=self).select_related("user").order_by("created_at", "id")


@type(
    CollaborationMention,
    fields=["id", "user", "created_at", "updated_at"],
)
class CollaborationMentionType(relay.Node, GetQuerysetMultiTenantMixin):
    user: Annotated["MultiTenantUserType", lazy("core.schema.multi_tenant.types.types")]
