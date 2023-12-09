from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser
from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List


@input(MultiTenantCompany)
class MultiTenantCompanyMyInput:
    name: auto
    country: auto
    phone_number: auto
    language: auto


@partial(MultiTenantCompany)
class MultiTenantCompanyMyPartialInput:
    name: auto
    country: auto
    phone_number: auto
    language: auto


@input(MultiTenantCompany, fields="__all__")
class MultiTenantCompanyInput:
    pass


@partial(MultiTenantCompany, exclude=['id'])
class MultiTenantCompanyPartialInput(NodeInput):
    pass


@input(MultiTenantUser)
class MultiTenantUserAcceptInviteInput:
    id: auto
    username: auto
    password: auto
    language: auto


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
    'avatar', 'is_active'])
class MultiTenantUserPartialInput:
    pass


@input(MultiTenantUser)
class MultiTenantInviteUserInput:
    username: auto
    language: auto
    first_name: auto
    last_name: auto
