from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_COMPANY, TAG_PRODUCTS, TAG_SALES_CHANNELS, TAG_SEARCH, tool_tags
from products.mcp.catalog_helpers import search_sales_channels_payload
from products.mcp.output_types import SEARCH_SALES_CHANNELS_OUTPUT_SCHEMA
from products.mcp.types import SearchSalesChannelsPayload


class SearchSalesChannelsMcpTool(BaseMcpTool):
    name = "search_sales_channels"
    title = "Search Sales Channels"
    read_only = True
    tags = tool_tags(TAG_SEARCH, TAG_PRODUCTS, TAG_COMPANY, TAG_SALES_CHANNELS)
    output_schema = SEARCH_SALES_CHANNELS_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        search: Annotated[str | None, Field(description="Optional hostname or marketplace-name substring to search for.")] = None,
        active: Annotated[bool | None, Field(description="Optional filter for active or inactive sales channels.")] = None,
        type: Annotated[str | None, Field(description="Optional integration type filter, for example magento, amazon, shopify, ebay, shein, mirakl, or woocommerce.")] = None,
        limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of sales channels to return.")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of matching sales channels to skip before returning results.")] = 0,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Search or list the sales channels configured for the authenticated company.
        Use this when you need to resolve a hostname or marketplace name to the
        exact sales_channel_id before calling channel-specific product tools.
        Each result also includes channel views. Use sales_channel_view_id when assigning
        a product to a storefront or website view. Use sales_channel_id for channel-specific
        content, images, prices, or other sales-channel-scoped product data.
        When called without filters, it returns the company sales channels as a paginated list.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_search = self._sanitize_optional_string(value=search)
            sanitized_active = self.sanitize_optional_bool(value=active, field_name="active")
            sanitized_type = self._sanitize_optional_string(value=type)
            sanitized_limit = self.sanitize_limit(limit=limit)
            sanitized_offset = self.sanitize_offset(offset=offset)
            response_data = await self._search_sales_channels(
                multi_tenant_company=multi_tenant_company,
                search=sanitized_search,
                active=sanitized_active,
                type_value=sanitized_type,
                limit=sanitized_limit,
                offset=sanitized_offset,
            )
            await ctx.info(
                f"Sales channel search returned {len(response_data['results'])} results; "
                f"total_count={response_data['total_count']}."
            )
            return self.build_result(
                summary=f"Found {response_data['total_count']} matching sales channel(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Search sales channels failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _search_sales_channels(
        self,
        *,
        multi_tenant_company,
        search: str | None,
        active: bool | None,
        type_value: str | None,
        limit: int,
        offset: int,
    ) -> SearchSalesChannelsPayload:
        return search_sales_channels_payload(
            multi_tenant_company=multi_tenant_company,
            search=search,
            active=active,
            type_value=type_value,
            limit=limit,
            offset=offset,
        )
