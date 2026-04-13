from __future__ import annotations

import json
from datetime import date, datetime


def serialize_value(*, value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def json_response(*, data):
    return json.dumps(data, indent=2, default=str)
