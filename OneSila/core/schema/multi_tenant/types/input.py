from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser, \
    MultiTenantUserLoginToken
from core.schema.core.types.types import auto
from core.schema.core.types.input import input, partial, strawberry_input


@input(MultiTenantCompany)
class MultiTenantCompanyMyInput:
    name: auto
    country: auto
    phone_number: auto
    language: auto


@input(MultiTenantCompany, fields="__all__")
class MultiTenantCompanyInput:
    pass


@partial(MultiTenantCompany, fields=['name', 'address1', 'address2', 'postcode', 'city', 'country',
    'language', 'email', 'phone_number', 'vat_number', 'website'])
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
class MultiTenantUserPartialInput:
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
