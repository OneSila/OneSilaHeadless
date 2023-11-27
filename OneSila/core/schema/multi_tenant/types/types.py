from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay, auto
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser

from typing import List


@type(MultiTenantUser, fields="__all__")
class MultiTenantUserType:
    # multi_tenant_company: auto
    pass


@type(MultiTenantCompany, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    multitenantuser_set: List[MultiTenantUserType]
