import strawberry


@strawberry.type
class LanguageType:
    bidi: bool
    code: str
    name: str
    name_local: str
    name_translated: str
