from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from llm.models import BrandCustomPrompt
from properties.schema.types.filters import PropertySelectValueFilter


@filter(BrandCustomPrompt)
class BrandCustomPromptFilter(SearchFilterMixin):
    id: auto
    language: auto
    brand_value: PropertySelectValueFilter | None
