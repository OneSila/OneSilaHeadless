from typing import List, Optional

from core.schema.core.types.types import relay, type, strawberry_type, GetQuerysetMultiTenantMixin
from .filters import BrandCustomPromptFilter
from .ordering import BrandCustomPromptOrder
from properties.schema.types.types import PropertySelectValueType
from llm.models import BrandCustomPrompt


@strawberry_type
class AiContent:
    content: str
    points: str
    bullet_point_index: Optional[int] = None


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


@type(
    BrandCustomPrompt,
    filters=BrandCustomPromptFilter,
    order=BrandCustomPromptOrder,
    pagination=True,
    fields="__all__",
)
class BrandCustomPromptType(relay.Node, GetQuerysetMultiTenantMixin):
    brand_value: PropertySelectValueType
