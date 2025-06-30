from typing import Optional, List

from core.schema.core.types.input import NodeInput, partial, strawberry_input
from products.models import Product
from enum import Enum

from products.schema.types.input import ProductPartialInput
from properties.schema.types.input import PropertyPartialInput, PropertySelectValuePartialInput


class ContentAiGenerateType(Enum):
    DESCRIPTION = "description"
    SHORT_DESCRIPTION = "short_description"
    NAME = "name"


@partial(Product, fields="__all__")
class ProductAiContentInput(NodeInput):
    language_code: str
    content_ai_generate_type: ContentAiGenerateType


@strawberry_input
class AITranslationInput:
    to_translate: str
    from_language_code: str
    to_language_code: str
    product: Optional[ProductPartialInput] = None
    product_content_type: Optional[ContentAiGenerateType] = None


@strawberry_input
class AIBulkTranslationInput:
    from_language_code: str
    to_language_codes: List[str]
    override_translation: Optional[bool] = False
    products: Optional[List[ProductPartialInput]] = None
    properties: Optional[List[PropertyPartialInput]] = None
    values: Optional[List[PropertySelectValuePartialInput]] = None


@partial(Product, fields="__all__")
class ProductAiBulletPointsInput(NodeInput):
    language_code: str
