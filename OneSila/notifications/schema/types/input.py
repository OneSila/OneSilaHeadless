from strawberry.relay import GlobalID
from strawberry.scalars import JSON

from core.schema.core.types.input import strawberry_input


@strawberry_input
class OpenNotificationInput:
    id: GlobalID


@strawberry_input
class CreateCollaborationEntryInput:
    target_id: GlobalID
    type: str
    comment: str | None = None
    metadata: JSON | None = None
    url: str | None = None
    mentioned_user_ids: list[GlobalID] | None = None
