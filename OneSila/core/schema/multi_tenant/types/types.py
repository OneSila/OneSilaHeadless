from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser

from typing import List


@type(MultiTenantUser, fields="__all__")
class MultiTenantUserType:
    pass


@type(MultiTenantCompany, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    multi_tenant_users: List[MultiTenantUserType]
