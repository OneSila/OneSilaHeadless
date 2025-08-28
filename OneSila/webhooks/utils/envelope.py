from typing import Dict, Any, Optional

from django.utils import timezone

from webhooks.constants import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_UPDATE,
    MODE_DELTA,
    MODE_FULL,
)


def build_envelope(
    integration,
    outbox,
    action: str,
    payload: Dict[str, Any],
    dirty_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    changed_fields = list(dirty_fields.keys()) if dirty_fields else []
    data: Dict[str, Any] = {}

    if action == ACTION_CREATE:
        mode = MODE_FULL
        data["after"] = payload
    elif action == ACTION_DELETE:
        mode = MODE_FULL
        data["before"] = payload
    elif action == ACTION_UPDATE:
        mode = integration.mode
        if mode == MODE_FULL:
            data["after"] = payload
            if dirty_fields:
                data["before"] = {k: dirty_fields[k] for k in changed_fields}
        else:  # MODE_DELTA
            if dirty_fields:
                data["after"] = {k: payload.get(k) for k in changed_fields}
                data["before"] = {k: dirty_fields[k] for k in changed_fields}
    else:
        mode = integration.mode

    if dirty_fields is not None:
        data["changed_fields"] = changed_fields

    subject = {"type": outbox.subject_type, "id": outbox.subject_id}
    if isinstance(payload, dict) and "sku" in payload:
        subject["sku"] = payload["sku"]

    return {
        "id": str(outbox.webhook_id),
        "event": outbox.topic,
        "action": action,
        "version": integration.version,
        "occurred_at": timezone.now().isoformat().replace("+00:00", "Z"),
        "subject": subject,
        "mode": mode,
        "data": data,
    }
