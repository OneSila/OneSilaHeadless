from strawberry_django import auth, field

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info

from typing import List

from core.countries import COUNTRY_CHOICES
from core.schema.languages.types.types import LanguageType
from django.conf import settings


def get_languages() -> List[LanguageType]:
    return [LanguageType(iso=iso, name=name) for iso, name in settings.LANGUAGES]


def get_default_language_code() -> str:
    return settings.LANGUAGE_CODE


@type(name="Query")
class LanguageQuery:
    default_language_code: str = field(resolver=get_default_language_code)
    languages: List[LanguageType] = field(resolver=get_languages)
