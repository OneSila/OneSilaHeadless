from django.contrib.auth import get_user_model

from core.schema.core.types.types import type, relay, auto
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from core.schema.multi_tenant.types.ordering import MultiTenantUserOrder
from core.schema.multi_tenant.types.filters import MultiTenantUserFilter
from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser

from strawberry_django.fields.types import DjangoImageType

from typing import List


@type(MultiTenantUser, filters=MultiTenantUserOrder, order=MultiTenantUserFilter, pagination=True, fields='__all__')
class MultiTenantUserType(relay.Node):
    avatar_resized: DjangoImageType


@type(MultiTenantCompany, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    multitenantuser_set: List[MultiTenantUserType]
