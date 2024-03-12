from core.schema.core.queries import type, anonymous_field
from translations.schema.types.types import TranslationLanguageType

from ..models import TranslationFieldsMixin

from typing import List

def get_translation_languages(info) -> List[TranslationLanguageType]:
    return [TranslationLanguageType(code=code, name=name) for code, name in TranslationFieldsMixin.LANGUAGES.ALL]

@type(name="Query")
class TranslationsQuery:
    translation_languages: List[TranslationLanguageType] = anonymous_field(resolver=get_translation_languages)

