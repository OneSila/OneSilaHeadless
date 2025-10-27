from typing import Annotated, List, Optional

from core.schema.core.types.types import relay, type, strawberry_type, GetQuerysetMultiTenantMixin
from strawberry.lazy import lazy

from .filters import BrandCustomPromptFilter
from .ordering import BrandCustomPromptOrder
from properties.schema.types.types import PropertySelectValueType
from llm.models import BrandCustomPrompt, ChatGptProductFeedConfig


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


@type(
    ChatGptProductFeedConfig,
    pagination=True,
    fields="__all__",
)
class ChatGptProductFeedConfigType(relay.Node, GetQuerysetMultiTenantMixin):
    condition_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    brand_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    material_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    length_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    width_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    height_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    weight_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    age_group_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    expiration_date_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    pickup_method_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    color_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    size_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    gender_system_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    popularity_score_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    warning_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]
    age_restriction_property: Optional[Annotated['PropertyType', lazy("properties.schema.types.types")]]

    condtion_new_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    condtion_refurbished_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    condtion_usd_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    age_group_newborn_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    age_group_infant_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    age_group_todler_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    age_group_kids_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    age_group_adult_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    pickup_method_in_store_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    pickup_method_reserve_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
    pickup_method_not_supported_value: Optional[Annotated['PropertySelectValueType', lazy("properties.schema.types.types")]]
