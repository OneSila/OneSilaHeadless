from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay, auto, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from typing import List


@strawberry_type
class LanguageType:
    bidi: bool
    code: str
    name: str
    name_local: str
    name_translated: str
