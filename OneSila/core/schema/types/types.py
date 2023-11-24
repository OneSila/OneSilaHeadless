from django.contrib.auth import get_user_model

from strawberry import relay, auto
from strawberry_django import type

from typing import List

from core.schema.mixins import GetQuerysetMultiTenantMixin
from core.models import MultiTenantCompany
