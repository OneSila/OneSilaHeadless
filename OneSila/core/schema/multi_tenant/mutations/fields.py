from core.schema.multi_tenant.types.input import MultiTenantCompanyMyInput, \
    MultiTenantCompanyPartialInput, MultiTenantUserPartialInput, \
    MultiTenantUserInput, MultiTenantInviteUserInput, MultiTenantUserAcceptInviteInput, \
    MultiTenantUserStatusInput, MultiTenantLoginLinkInput, MultiTenantUserAuthenticateTokenInput
from core.schema.core.mutations import IsAuthenticated, default_extensions
from .mutation_classes import MyMultiTenantCompanyCreateMutation, \
    MyMultiTentantCompanyUpdateMutation, UpdateMeMutation, \
    RegisterUserMutation, InviteUserMutation, AcceptInvitationMutation, \
    EnableUserMutation, DisableUserMutation, LoginTokenMutation, RecoveryTokenMutation, \
    AuthenticateTokenMutation


def register_my_multi_tenant_company():
    extensions = [IsAuthenticated()]
    return MyMultiTenantCompanyCreateMutation(MultiTenantCompanyMyInput, extensions=extensions)


def update_my_multi_tenant_company():
    extensions = default_extensions
    return MyMultiTentantCompanyUpdateMutation(MultiTenantCompanyPartialInput, extensions=extensions)


def update_me():
    extensions = [IsAuthenticated()]
    return UpdateMeMutation(MultiTenantUserPartialInput, extensions=extensions)


def register_user():
    extensions = []
    return RegisterUserMutation(MultiTenantUserInput, extensions=extensions)


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


def authenticate_token():
    extensions = []
    return AuthenticateTokenMutation(MultiTenantUserAuthenticateTokenInput, extensions=extensions)
