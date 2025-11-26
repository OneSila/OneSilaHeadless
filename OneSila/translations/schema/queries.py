from core.schema.core.helpers import get_multi_tenant_company
from core.schema.core.queries import type, field
from translations.schema.types.types import TranslationLanguageType, TranslationLanguageWithDefaultType

from ..models import TranslationFieldsMixin

from typing import List


def get_translation_languages_with_default(info) -> TranslationLanguageWithDefaultType:
    multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
    default_language_code = multi_tenant_company.language
    default_language_name = dict(TranslationFieldsMixin.LANGUAGES).get(default_language_code, "Unknown")

    # Filter LANGUAGES based on what's in multi_tenant_company.languages
    allowed_codes = set(multi_tenant_company.languages or [default_language_code])
    available_languages = [
        (code, name) for code, name in TranslationFieldsMixin.LANGUAGES if code in allowed_codes
    ]

    languages = [
        TranslationLanguageType(code=code, name=name)
        for code, name in available_languages
    ]

    default_language = TranslationLanguageType(code=default_language_code, name=default_language_name)

    return TranslationLanguageWithDefaultType(
        languages=languages,
        default_language=default_language
    )


@type(name="Query")
class TranslationsQuery:
    translation_languages: TranslationLanguageWithDefaultType = field(resolver=get_translation_languages_with_default)
