from core.schema.core.types.types import strawberry_type

@strawberry_type
class AiContent:
    content: str
    points: str