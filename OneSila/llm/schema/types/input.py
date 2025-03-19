from typing import Optional

from core.schema.core.types.input import NodeInput, partial, strawberry_input
from products.models import Product
from enum import Enum

from products.schema.types.input import ProductPartialInput


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