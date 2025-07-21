from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from llm.models import BrandCustomPrompt


@order(BrandCustomPrompt)
class BrandCustomPromptOrder:
    id: auto
    language: auto
