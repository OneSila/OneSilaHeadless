from typing import Optional, List

from core.schema.core.types.input import NodeInput, partial, strawberry_input, input
from products.models import Product
from enum import Enum
from integrations.constants import (
    MAGENTO_INTEGRATION,
    SHOPIFY_INTEGRATION,
    AMAZON_INTEGRATION,
    WOOCOMMERCE_INTEGRATION,
)

from products.schema.types.input import ProductPartialInput
from properties.schema.types.input import (
    PropertyPartialInput,
    PropertySelectValuePartialInput,
)
from llm.models import BrandCustomPrompt, ChatGptProductFeedConfig
from sales_channels.schema.types.input import SalesChannelPartialInput


class ContentAiGenerateType(Enum):
    DESCRIPTION = "description"
    SHORT_DESCRIPTION = "short_description"
    SUBTITLE = "subtitle"
    NAME = "name"
    BULLET_POINTS = "bullet_points"


class SalesChannelIntegrationType(Enum):
    MAGENTO = MAGENTO_INTEGRATION
    SHOPIFY = SHOPIFY_INTEGRATION
    AMAZON = AMAZON_INTEGRATION
    WOOCOMMERCE = WOOCOMMERCE_INTEGRATION


@partial(Product, fields="__all__")
class ProductAiContentInput(NodeInput):
    language_code: str
    content_ai_generate_type: ContentAiGenerateType
    sales_channel_type: Optional[SalesChannelIntegrationType] = None


@strawberry_input
class AITranslationInput:
    to_translate: str
    from_language_code: str
    to_language_code: str
    product: Optional[ProductPartialInput] = None
    product_content_type: Optional[ContentAiGenerateType] = None
    sales_channel: Optional[SalesChannelPartialInput] = None
    return_one_bullet_point: Optional[bool] = False
    bullet_point_index: Optional[int] = None


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
    return_one: Optional[bool] = False


@input(BrandCustomPrompt, fields="__all__")
class BrandCustomPromptInput:
    pass


@partial(BrandCustomPrompt, fields="__all__")
class BrandCustomPromptPartialInput(NodeInput):
    pass


@input(ChatGptProductFeedConfig, fields="__all__")
class ChatGptProductFeedConfigInput:
    pass


@partial(ChatGptProductFeedConfig, fields="__all__")
class ChatGptProductFeedConfigPartialInput(NodeInput):
    pass
