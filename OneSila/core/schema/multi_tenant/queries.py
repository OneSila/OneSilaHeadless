from strawberry_django import auth, field

from core.models.multi_tenant import MultiTenantCompany
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info
from core.schema.core.helpers import get_multi_tenant_company
from .types.types import MultiTenantUserType, MultiTenantCompanyType


from strawberry_django.fields.field import StrawberryDjangoField
from strawberry import relay


def resolve_my_multi_tenant_company_node(info: Info) -> MultiTenantCompany:
    multi_tenant_company = get_multi_tenant_company(info)
    return multi_tenant_company


def my_multi_tenant_company_node(*args, **kwargs):
    return field(resolver=resolve_my_multi_tenant_company_node)


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()

    # FIXME: You shouldn't be able to fetch the multi_tenant_company from
    # another user.  And you should receive the right company by default.
    # eg field my_multi_tenant_company instead of the default multi_tenant_company node.
    # multi_tenant_company: MultiTenantCompanyType = node()
    my_multi_tenant_company: MultiTenantCompanyType = my_multi_tenant_company_node()
