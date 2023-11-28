from strawberry_django import auth, field

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info


def my_multi_tenant_company_resolver(info: Info) -> MultiTenantCompanyType:
    multi_tenant_company = get_multi_tenant_company(info)
    return multi_tenant_company


def my_multi_tenant_company(*args, **kwargs):
    return field(resolver=my_multi_tenant_company_resolver)


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()
    my_multi_tenant_company: MultiTenantCompanyType = my_multi_tenant_company()
