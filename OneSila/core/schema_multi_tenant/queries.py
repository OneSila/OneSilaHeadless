from strawberry_django import auth

from core.schema.queries import node, connection, ListConnectionWithTotalCount, type, field
from .types.types import MultiTenantUserType, MultiTenantCompanyType


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()

    # FIXME: You shouldn't be able to fetch the multi_tenant_company from
    # another user.  And you should receive the right company by default.
    # eg field my_multi_tenant_company instead of the default multi_tenant_company node.
    multi_tenant_company: MultiTenantCompanyType = node()
