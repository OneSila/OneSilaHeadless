from strawberry_django import auth, field

from django.utils import timezone

from core.schema.core.queries import type, field, anonymous_field

from typing import List

from core.schema.timezones.types.types import TimeZoneType
from core.schema.core.helpers import get_current_user

from pytz import all_timezones


def get_timezones(info) -> List[TimeZoneType]:
    timezones = [TimeZoneType(key=key) for key in all_timezones]
    return timezones


def get_default_timezone() -> TimeZoneType:
    return TimeZoneType(key=timezone.get_default_timezone().key)


def get_current_user_timezone(info) -> TimeZoneType:
    user = get_current_user(info)
    tz = TimeZoneType(key=user.timezone)
    return tz


@type(name="Query")
class TimeZoneQuery:
    default_timezone: TimeZoneType = anonymous_field(resolver=get_default_timezone)
    current_user_timezone: TimeZoneType = field(resolver=get_current_user_timezone)
    timezones: List[TimeZoneType] = anonymous_field(resolver=get_timezones)
