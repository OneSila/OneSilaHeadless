from core.schema.core.mutations import type
from strawberry_django import auth as strawberry_auth
from .fields import (
    register_my_multi_tenant_company,
    update_me,
    update_my_multi_tenant_company,
    invite_user,
    accept_user_invitation,
    disable_user,
    enable_user,
    request_login_token,
    recovery_token,
    authenticate_token,
    register_user,
    update_my_password,
    go_to_step,
    create_demo_data,
    delete_demo_data,
    resend_invite,
    create_dashboard_section,
    create_dashboard_card,
    update_dashboard_section,
    delete_dashboard_section,
    update_dashboard_card,
    delete_dashboard_card,
)

from core.schema.multi_tenant.types.types import MultiTenantUserType, \
    MultiTenantCompanyType, MultiTenantUserLoginTokenType, DashboardSectionType, DashboardCardType


@type(name="Mutation")
class MultiTenantMutation:
    login: MultiTenantUserType = strawberry_auth.login()
    logout = strawberry_auth.logout()

    register_user: MultiTenantUserType = register_user()
    register_my_multi_tenant_company: MultiTenantCompanyType = register_my_multi_tenant_company()

    update_me: MultiTenantUserType = update_me()
    update_my_password: MultiTenantUserType = update_my_password()
    update_my_multi_tenant_company: MultiTenantCompanyType = update_my_multi_tenant_company()

    recovery_token: MultiTenantUserLoginTokenType = recovery_token()
    request_login_token: MultiTenantUserLoginTokenType = request_login_token()
    authenticate_token: MultiTenantUserType = authenticate_token()

    invite_user: MultiTenantUserType = invite_user()
    accept_user_invitation: MultiTenantUserType = accept_user_invitation()
    resend_invite: MultiTenantUserType = resend_invite()

    disable_user: MultiTenantUserType = disable_user()
    enable_user: MultiTenantUserType = enable_user()

    go_to_step: MultiTenantUserType = go_to_step()
    create_demo_data: MultiTenantCompanyType = create_demo_data()
    delete_demo_data: MultiTenantCompanyType = delete_demo_data()
    create_dashboard_section: DashboardSectionType = create_dashboard_section()
    update_dashboard_section: DashboardSectionType = update_dashboard_section()
    delete_dashboard_section: DashboardSectionType = delete_dashboard_section()
    create_dashboard_card: DashboardCardType = create_dashboard_card()
    update_dashboard_card: DashboardCardType = update_dashboard_card()
    delete_dashboard_card: DashboardCardType = delete_dashboard_card()
