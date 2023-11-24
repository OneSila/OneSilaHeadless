from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser
from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial, List


@input(MultiTenantCompany)
class MultiTenantCompanyInput:
    name: auto
    address1: auto
    address2: auto
    postcode: auto
    city: auto
    country: auto
    language: auto
    email: auto
    phone_number: auto
    vat_number: auto
    website: auto


@partial(MultiTenantCompany)
class MultiTenantCompanyPartialInput:
    id: auto
    name: auto
    address1: auto
    address2: auto
    postcode: auto
    city: auto
    country: auto
    language: auto
    email: auto
    phone_number: auto
    vat_number: auto
    website: auto


@input(MultiTenantUser)
class MultiTenantUserInput:
    username: auto
    password: auto
    language: auto
    first_name: auto
    last_name: auto


@partial(MultiTenantUser)
class MultiTenantUserPartialInput:
    id: auto
    username: auto
    password: auto
    language: auto
    first_name: auto
    last_name: auto
