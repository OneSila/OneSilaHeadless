from core.schema.core.types.types import strawberry_type


@strawberry_type
class CountryType:
    code: str
    name: str
