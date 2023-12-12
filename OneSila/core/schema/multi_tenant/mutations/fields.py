from core.schema.multi_tenant.types.input import MultiTenantCompanyMyInput, \
    MultiTenantCompanyPartialInput, MultiTenantUserPartialInput, \
    MultiTenantUserInput, MultiTenantInviteUserInput, MultiTenantUserAcceptInviteInput, \
    MultiTenantUserStatusInput, MultiTenantLoginLinkInput, MultiTenantUserAuthenticateTokenInput, \
    MultiTenantCompanyMyPartialInput

from core.schema.core.mutations import IsAuthenticated, default_extensions
from .mutation_classes import MyMultiTenantCompanyCreateMutation, \
    MyMultiTentantCompanyUpdateMutation, UpdateMeMutation, \
    InviteUserMutation, AcceptInvitationMutation, EnableUserMutation, \
    DisableUserMutation, LoginTokenMutation, RecoveryTokenMutation

import functools
import strawberry
from .resolvers import resolve_register_user, resolve_authenticate_token


def register_my_multi_tenant_company():
    extensions = [IsAuthenticated()]
    return MyMultiTenantCompanyCreateMutation(MultiTenantCompanyMyInput, extensions=extensions)


def update_my_multi_tenant_company():
    extensions = default_extensions
    return MyMultiTentantCompanyUpdateMutation(MultiTenantCompanyMyPartialInput, extensions=extensions)


def update_me():
    extensions = [IsAuthenticated()]
    return UpdateMeMutation(MultiTenantUserPartialInput, extensions=extensions)


def invite_user():
    extensions = default_extensions
    return InviteUserMutation(MultiTenantInviteUserInput, extensions=extensions)


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


def login_token():
    extensions = []
    return RecoveryTokenMutation(MultiTenantLoginLinkInput, extensions=extensions)


register_user = functools.partial(strawberry.mutation, resolver=resolve_register_user)
authenticate_token = functools.partial(strawberry.mutation, resolver=resolve_authenticate_token)
