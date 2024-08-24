from core.schema.core.types.types import strawberry_type, List


@strawberry_type
class TranslationLanguageType:
    code: str
    name: str


@strawberry_type
class TranslationLanguageWithDefaultType:
    languages: List[TranslationLanguageType]
    default_language: TranslationLanguageType
