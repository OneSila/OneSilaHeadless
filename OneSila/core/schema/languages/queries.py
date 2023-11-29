from strawberry_django import auth, field

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.multi_tenant.types.types import MultiTenantUserType, MultiTenantCompanyType
from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, \
    type, field, default_extensions, Info, anonymous_field

from typing import List

from core.countries import COUNTRY_CHOICES
from core.schema.languages.types.types import LanguageType
from core.schema.core.helpers import get_current_user
from django.conf import settings
from django.utils.translation import activate, get_language_info, deactivate


def get_languages(info) -> List[LanguageType]:
    user = get_current_user(info)
    activate(user.language)
    languages = [LanguageType(**get_language_info(code)) for code, _ in settings.LANGUAGES]
    deactivate()
    return languages


def get_default_language() -> LanguageType:
    return LanguageType(**get_language_info(settings.LANGUAGE_CODE))


def get_current_user_language(info) -> LanguageType:
    user = get_current_user(info)
    activate(user.language)
    lang = LanguageType(**get_language_info(user.language))
    deactivate()
    return lang


@type(name="Query")
class LanguageQuery:
    default_language: LanguageType = anonymous_field(resolver=get_default_language)
    current_user_language: LanguageType = field(resolver=get_current_user_language)
    languages: List[LanguageType] = anonymous_field(resolver=get_languages)
