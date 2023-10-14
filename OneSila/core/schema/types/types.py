from strawberry import relay, auto
from strawberry_django import type

from typing import List

from core.schema.mixins import GetQuerysetMultiTenantMixin
from core.models import MultiTenantCompany


@type(MultiTenantCompany, pagination=False, fields='__all__')
class MultiTenantCompanyType(relay.Node):
    pass
