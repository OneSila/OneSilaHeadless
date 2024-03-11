from core.schema.core.types.types import strawberry_type

@strawberry_type
class TranslationLanguageType:
    code: str
    name: str