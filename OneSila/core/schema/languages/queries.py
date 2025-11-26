from strawberry_django import auth, field

from django.contrib.auth.models import AnonymousUser

from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.queries import type, field, anonymous_field

from typing import List

from core.schema.languages.types.types import LanguageType
from core.schema.core.helpers import get_current_user
from django.conf import settings
from django.utils.translation import activate, get_language_info, deactivate


def get_languages(info) -> List[LanguageType]:
    user = get_current_user(info)

    if not user.is_anonymous:
        activate(user.language)

    languages = [LanguageType(**get_language_info(code)) for code, _ in settings.LANGUAGES]

    if not user.is_anonymous:
        deactivate()

    return languages


def get_interface_languages(info) -> List[LanguageType]:
    user = get_current_user(info)

    if not user.is_anonymous:
        activate(user.language)

    languages = [LanguageType(**get_language_info(code)) for code, _ in settings.INTERFACE_LANGUAGES]

    if not user.is_anonymous:
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


def get_company_languages(info) -> List[LanguageType]:
    user = get_current_user(info)
    activate(user.language)

    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    allowed_codes = set(multi_tenant_company.languages or [multi_tenant_company.language])

    languages = [
        LanguageType(**get_language_info(code))
        for code, _ in settings.LANGUAGES
        if code in allowed_codes
    ]

    deactivate()
    return languages


@type(name="Query")
class LanguageQuery:
    default_language: LanguageType = anonymous_field(resolver=get_default_language)
    current_user_language: LanguageType = field(resolver=get_current_user_language)
    languages: List[LanguageType] = anonymous_field(resolver=get_languages)
    interface_languages: List[LanguageType] = anonymous_field(resolver=get_interface_languages)
    company_languages: List[LanguageType] = field(resolver=get_company_languages)
