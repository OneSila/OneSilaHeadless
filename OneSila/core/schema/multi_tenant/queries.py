from strawberry_django import auth, field

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info, List


def my_multi_tenant_company_resolver(info: Info) -> MultiTenantCompanyType:
    multi_tenant_company = get_multi_tenant_company(info)
    return multi_tenant_company


def users_resolver(info: Info) -> List[MultiTenantUserType]:
    multi_tenant_company = get_multi_tenant_company(info)
    users = multi_tenant_company.multitenantuser_set.all()
    return users


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()
    my_multi_tenant_company: MultiTenantCompanyType = field(resolver=my_multi_tenant_company_resolver)
    users: List[MultiTenantUserType] = field(resolver=users_resolver)
