from strawberry_django import auth

from core.schema.mutations import create, update, delete, type, List, field
from .types.types import MultiTenantUserType, MultiTenantCompanyType
from .types.input import MultiTenantUserInput, MultiTenantUserPartialInput, \
    MultiTenantCompanyPartialInput, MultiTenantCompanyInput


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = auth.login()
    logout = auth.logout()
    register_user: MultiTenantUserType = auth.register(MultiTenantUserInput)
    register_multi_tenant_company: MultiTenantCompanyType = create(MultiTenantUserInput)

    # FIXME: You should only be able to update yourself. Not other users. (unless it's to disable)
    update_user: MultiTenantUserType = update(MultiTenantUserPartialInput)

    # FIXME: You should only be able to update your own multi tenant company. Not other users. (unless it's to disable)
    update_multi_tenant_company: MultiTenantCompanyType = update(MultiTenantCompanyPartialInput)
