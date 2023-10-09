from strawberry import relay, auto
from strawberry_django import type

from typing import List

from core.schema.mixins import GetQuerysetMultiTenantMixin
from django_shared_multi_tenant.schema import MultiTenantCompanyType
