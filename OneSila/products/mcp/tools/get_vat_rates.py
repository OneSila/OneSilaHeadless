from __future__ import annotations

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from products.mcp.catalog_helpers import get_vat_rates_payload
from products.mcp.output_types import GET_VAT_RATES_OUTPUT_SCHEMA
from products.mcp.types import GetVatRatesPayload


class GetVatRatesMcpTool(BaseMcpTool):
    name = "get_vat_rates"
    title = "Get VAT Rates"
    read_only = True
    output_schema = GET_VAT_RATES_OUTPUT_SCHEMA
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
        List the VAT rates configured for the authenticated company.
        Use these values before create_product when you want to attach a VAT rate at creation time.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            response_data: GetVatRatesPayload = get_vat_rates_payload(
                multi_tenant_company=multi_tenant_company,
            )
            await ctx.info(
                f"Loaded {response_data['count']} VAT rates for company_id={multi_tenant_company.id}."
            )
            return self.build_result(
                summary=f"Company has {response_data['count']} VAT rate option(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get VAT rates failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise
