from strawberry.relay import GlobalID

from core.schema.core.helpers import get_current_user
from core.schema.core.queries import type, connection, DjangoListConnection, field

from notifications.models import Notification

from .helpers import get_collaboration_thread
from .types.types import CollaborationThreadType, NotificationType


def collaboration_thread_by_target_resolver(info, target_id: GlobalID) -> CollaborationThreadType | None:
    return get_collaboration_thread(info=info, target_id=target_id)


@type(name="Query")
class NotificationsQuery:
    collaboration_thread_by_target: CollaborationThreadType | None = field(
        resolver=collaboration_thread_by_target_resolver
    )
    notifications: DjangoListConnection[NotificationType] = connection()
