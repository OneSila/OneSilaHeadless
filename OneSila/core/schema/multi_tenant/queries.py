from strawberry_django import auth, field

from core.models.multi_tenant import MultiTenantCompany
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info
from core.schema.core.helpers import get_multi_tenant_company
from .types.types import MultiTenantUserType, MultiTenantCompanyType


from strawberry_django.fields.field import StrawberryDjangoField
from strawberry import relay


def my_multi_tenant_company_resolver(info: Info) -> MultiTenantCompany:
    multi_tenant_company = get_multi_tenant_company(info)
    return multi_tenant_company


def my_multi_tenant_company(*args, **kwargs):
    return field(resolver=my_multi_tenant_company_resolver)


@type(name="Query")
class MultiTenantQuery:
    me: MultiTenantUserType = auth.current_user()
    my_multi_tenant_company: MultiTenantCompanyType = my_multi_tenant_company()
