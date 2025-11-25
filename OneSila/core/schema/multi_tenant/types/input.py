from core.models.multi_tenant import (
    MultiTenantCompany,
    MultiTenantUser,
    MultiTenantUserLoginToken,
    DashboardSection,
    DashboardCard,
)
from core.schema.core.types.types import auto
from core.schema.core.types.input import input, partial, strawberry_input, NodeInput
from strawberry.relay import GlobalID


@input(MultiTenantCompany)
class MultiTenantCompanyMyInput:
    name: auto
    country: auto
    phone_number: str | None
    language: str | None


@input(MultiTenantCompany, fields="__all__")
class MultiTenantCompanyInput:
    pass


@partial(MultiTenantCompany, fields=['name', 'address1', 'address2', 'postcode', 'city', 'country',
    'languages', 'email', 'phone_number', 'vat_number', 'website'])
class MultiTenantCompanyPartialInput:
    pass


@input(MultiTenantUser, fields=['password', 'language'])
class MultiTenantUserAcceptInviteInput:
    pass


@partial(MultiTenantUser, fields=['password'])
class MultiTenantUserPasswordInput:
    pass


@input(MultiTenantUser)
class MultiTenantUserInput:
    username: auto
    password: auto
    language: auto


@input(MultiTenantUser)
class MultiTenantUserStatusInput:
    id: auto


@partial(MultiTenantUser, fields=['username', 'is_multi_tenant_company_owner',
    'language', 'timezone', 'mobile_number', 'whatsapp_number', 'telegram_number',
    'avatar', 'is_active', 'first_name', 'last_name'])
class MeMultiTenantUserPartialInput:
    pass


@partial(MultiTenantUser, fields=['multi_tenant_company', 'id', 'first_name', 'last_name', 'email', 'is_active'])
class MultiTenantUserPartialInput(NodeInput):
    pass


@input(MultiTenantUser)
class MultiTenantInviteUserInput:
    username: auto
    language: auto
    first_name: auto
    last_name: auto


@strawberry_input
class MultiTenantLoginLinkInput:
    username: str


@strawberry_input
class MultiTenantUserLoginTokenInput:
    username: str


@strawberry_input
class UpdateOnboardingStatusInput:
    onboarding_status: str


@partial(MultiTenantUserLoginToken)
class MultiTenantUserAuthenticateTokenInput:
    token: auto


@input(DashboardSection, fields="__all__")
class DashboardSectionInput:
    pass

@partial(DashboardSection, fields="__all__")
class DashboardSectionPartialInput(NodeInput):
    pass


@input(DashboardCard, fields="__all__")
class DashboardCardInput:
    pass


@partial(DashboardCard, fields="__all__")
class DashboardCardPartialInput(NodeInput):
    pass
