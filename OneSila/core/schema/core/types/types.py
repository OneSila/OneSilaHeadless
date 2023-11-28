from django.contrib.auth import get_user_model

from strawberry import relay, auto
from strawberry import type as strawberry_type
from strawberry_django import type

from typing import List

from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.models import MultiTenantCompany
