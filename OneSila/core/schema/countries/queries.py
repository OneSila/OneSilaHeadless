from strawberry_django import auth

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, anonymous_field, default_extensions, Info

from typing import List

from core.countries import COUNTRY_CHOICES
from core.schema.countries.types.types import CountryType


def get_countries() -> List[CountryType]:
    return [CountryType(code=code, name=name) for code, name in COUNTRY_CHOICES]


@type(name="Query")
class CountryQuery:
    countries: List[CountryType] = anonymous_field(resolver=get_countries)
