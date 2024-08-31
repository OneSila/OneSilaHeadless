from django.contrib.auth import get_user_model

from strawberry import relay, auto, lazy
from strawberry import type as strawberry_type
from strawberry_django import type
from strawberry_django import field
from strawberry.lazy_type import LazyType as strawberry_lazy
from typing import List, Annotated

from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.models import MultiTenantCompany
