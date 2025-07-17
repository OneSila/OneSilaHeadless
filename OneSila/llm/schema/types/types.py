from typing import List

from core.schema.core.types.types import strawberry_type


@strawberry_type
class AiContent:
    content: str
    points: str


@strawberry_type
class AiTaskResponse:
    success: bool


@strawberry_type
class BulletPoint:
    text: str


@strawberry_type
class AiBulletPoints:
    bullet_points: List[BulletPoint]
    points: str
