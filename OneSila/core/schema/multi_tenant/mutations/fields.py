import functools

from django.core.exceptions import PermissionDenied, ValidationError
import strawberry

from core.schema.multi_tenant.types.input import (
    MultiTenantCompanyMyInput,
    MultiTenantCompanyPartialInput,
    MeMultiTenantUserPartialInput,
    MultiTenantUserInput,
    MultiTenantInviteUserInput,
    MultiTenantUserAcceptInviteInput,
    MultiTenantUserStatusInput,
    MultiTenantLoginLinkInput,
    MultiTenantUserPasswordInput,
    MultiTenantUserAuthenticateTokenInput,
    UpdateOnboardingStatusInput,
    DashboardSectionInput,
    DashboardSectionPartialInput,
    DashboardCardInput,
    DashboardCardPartialInput,
)

from core.schema.core.helpers import get_current_user
from core.schema.core.mutations import IsAuthenticated, default_extensions, create, update, delete
from core.schema.multi_tenant.extensions import IsMultiTenantCompanyOwner
from .mutation_classes import MyMultiTenantCompanyCreateMutation, \
    MyMultiTentantCompanyUpdateMutation, UpdateMeMutation, \
    InviteUserMutation, AcceptInvitationMutation, EnableUserMutation, \
    DisableUserMutation, RequestLoginTokenMutation, RecoveryTokenMutation, \
    UpdateMyPasswordMutation, UpdateOnboardingStatusMutation, CreateDemoDataMutation, \
    DeleteDemoDataMutation, ResendInviteMutation

from .resolvers import resolve_register_user, resolve_authenticate_token


def register_my_multi_tenant_company():
    extensions = [IsAuthenticated()]
    return MyMultiTenantCompanyCreateMutation(MultiTenantCompanyMyInput, extensions=extensions)


def update_my_multi_tenant_company():
    extensions = [*default_extensions, IsMultiTenantCompanyOwner()]
    return MyMultiTentantCompanyUpdateMutation(MultiTenantCompanyPartialInput, extensions=extensions)


def update_me():
    extensions = [IsAuthenticated()]
    return UpdateMeMutation(MeMultiTenantUserPartialInput, extensions=extensions)


def update_my_password():
    extensions = [IsAuthenticated()]
    return UpdateMyPasswordMutation(MultiTenantUserPasswordInput, extensions=extensions)


def invite_user():
    extensions = default_extensions
    return InviteUserMutation(MultiTenantInviteUserInput, extensions=extensions)


def resend_invite():
    extensions = default_extensions
    return ResendInviteMutation(MultiTenantUserStatusInput, extensions=extensions)


def accept_user_invitation():
    extensions = []
    return AcceptInvitationMutation(MultiTenantUserAcceptInviteInput, extensions=extensions)


def disable_user():
    extensions = default_extensions
    return DisableUserMutation(MultiTenantUserStatusInput, extensions=extensions)


def enable_user():
    extensions = default_extensions
    return EnableUserMutation(MultiTenantUserStatusInput, extensions=extensions)


def recovery_token():
    extensions = []
    return RecoveryTokenMutation(MultiTenantLoginLinkInput, extensions=extensions)


def request_login_token():
    extensions = []
    return RequestLoginTokenMutation(MultiTenantLoginLinkInput, extensions=extensions)


def go_to_step():
    extensions = default_extensions
    return UpdateOnboardingStatusMutation(UpdateOnboardingStatusInput, extensions=extensions)


def create_demo_data():
    extensions = default_extensions
    return CreateDemoDataMutation(extensions=extensions)


def delete_demo_data():
    extensions = default_extensions
    return DeleteDemoDataMutation(extensions=extensions)


def _validate_dashboard_user_assignment(data, info):
    current_user = get_current_user(info)
    if current_user is None:
        raise PermissionDenied("Missing authenticated user.")

    target_user = data.get("user").pk
    if target_user is None:
        data["user"] = current_user
        return

    if target_user == current_user:
        return

    if target_user.multi_tenant_company_id != current_user.multi_tenant_company_id:
        raise PermissionDenied("Cannot create dashboards for users in another company.")

    if not current_user.is_multi_tenant_company_owner:
        raise PermissionDenied("Only company owners can create dashboards for other users.")


def _validate_dashboard_card_section(data, info):
    section = data.get("section").pk
    user = data.get("user").pk

    if section is None:
        raise ValidationError({"section": "A dashboard section is required."})

    if user is None:
        user = get_current_user(info)
        data["user"] = user

    if section.user_id != user.id:
        raise ValidationError({"user": "Dashboard card user must match the section owner."})

    if section.multi_tenant_company_id != user.multi_tenant_company_id:
        raise ValidationError({"section": "Section must belong to the same company as the user."})


def create_dashboard_section():
    extensions = default_extensions
    validators = [_validate_dashboard_user_assignment]
    return create(DashboardSectionInput, validators=validators)


def create_dashboard_card():
    extensions = default_extensions
    validators = [_validate_dashboard_user_assignment, _validate_dashboard_card_section]
    return create(DashboardCardInput, validators=validators)


def update_dashboard_section():
    return update(DashboardSectionPartialInput)


def delete_dashboard_section():
    return delete()


def update_dashboard_card():
    return update(DashboardCardPartialInput)


def delete_dashboard_card():
    return delete()


register_user = functools.partial(strawberry.mutation, resolver=resolve_register_user)
authenticate_token = functools.partial(strawberry.mutation, resolver=resolve_authenticate_token)
