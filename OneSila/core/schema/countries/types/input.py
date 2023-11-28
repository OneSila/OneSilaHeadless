from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser
from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List


@input(MultiTenantCompany)
class MultiTenantCompanyMyInput:
    name: auto
    country: auto
    phone_number: auto
    language: auto


@input(MultiTenantCompany, fields="__all__")
class MultiTenantCompanyInput:
    pass


@partial(MultiTenantCompany, fields="__all__")
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


@partial(MultiTenantUser, fields="__all__")
class MultiTenantUserPartialInput:
    pass


@input(MultiTenantUser)
class MultiTenantInviteUserInput:
    username: auto
    language: auto
    first_name: auto
    last_name: auto
