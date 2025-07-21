from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import BrandCustomPromptType


@type(name="Query")
class LlmQuery:
    brand_custom_prompt: BrandCustomPromptType = node()
    brand_custom_prompts: DjangoListConnection[BrandCustomPromptType] = connection()
