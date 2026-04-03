from __future__ import annotations

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from products.mcp.catalog_helpers import get_product_types_payload
from products.mcp.output_types import GET_PRODUCT_TYPES_OUTPUT_SCHEMA
from products.mcp.types import GetProductTypesPayload


class GetProductTypesMcpTool(BaseMcpTool):
    name = "get_product_types"
    title = "Get Product Types"
    read_only = True
    output_schema = GET_PRODUCT_TYPES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        List the available product-type values for the authenticated company.
        These values come from the company's product-type property select values and can be
        used in create_product via product_type_id.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            response_data = await self._get_product_types(
                multi_tenant_company=multi_tenant_company,
            )
            await ctx.info(
                f"Loaded {response_data['count']} product types for company_id={multi_tenant_company.id}."
            )
            return self.build_result(
                summary=(
                    f"Company has {response_data['count']} product type value(s) on "
                    f"property '{response_data['property']['name']}'."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get product types failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_product_types(
        self,
        *,
        multi_tenant_company,
    ) -> GetProductTypesPayload:
        try:
            return get_product_types_payload(
                multi_tenant_company=multi_tenant_company,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
