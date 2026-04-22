from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import BrandCustomPromptType, ChatGptProductFeedConfigType, McpToolRunType


@type(name="Query")
class LlmQuery:
    brand_custom_prompt: BrandCustomPromptType = node()
    brand_custom_prompts: DjangoListConnection[BrandCustomPromptType] = connection()
    mcp_tool_run: McpToolRunType = node()
    mcp_tool_runs: DjangoListConnection[McpToolRunType] = connection()
    chat_gpt_product_feed_config: ChatGptProductFeedConfigType = node()
    chat_gpt_product_feed_configs: DjangoListConnection[ChatGptProductFeedConfigType] = connection()
