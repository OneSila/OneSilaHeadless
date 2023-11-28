from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay, auto, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin


@strawberry_type
class CountryType:
    code: str
    name: str
