from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from llm.models import BrandCustomPrompt, McpToolRun


@order(BrandCustomPrompt)
class BrandCustomPromptOrder:
    id: auto
    language: auto


@order(McpToolRun)
class McpToolRunOrder:
    id: auto
    tool_name: auto
    status: auto
    created_at: auto
