from core.schema.core.mutations import type
from strawberry_django import auth as strawberry_auth
from .fields import register_my_multi_tenant_company, \
    update_me, update_my_multi_tenant_company, invite_user, \
    accept_user_invitation, disable_user, enable_user, login_token, \
    recovery_token, authenticate_token, register_user

from core.schema.multi_tenant.types.types import MultiTenantUserType, \
    MultiTenantCompanyType, MultiTenantUserLoginTokenType


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = strawberry_auth.login()
    logout = strawberry_auth.logout()

    register_user: MultiTenantUserType = register_user()
    register_my_multi_tenant_company: MultiTenantCompanyType = register_my_multi_tenant_company()

    update_me: MultiTenantUserType = update_me()
    update_my_multi_tenant_company: MultiTenantCompanyType = update_my_multi_tenant_company()

    recovery_token: MultiTenantUserLoginTokenType = recovery_token()
    login_token: MultiTenantUserLoginTokenType = login_token()
    authenticate_token: MultiTenantUserType = authenticate_token()

    invite_user: MultiTenantUserType = invite_user()
    accept_user_invitation: MultiTenantUserType = accept_user_invitation()

    disable_user: MultiTenantUserType = disable_user()
    enable_user: MultiTenantUserType = enable_user()
