from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from products.mcp.output_types import PRODUCT_MUTATION_OUTPUT_SCHEMA
from products.mcp.types import ProductMutationPayload
from products.mcp.update_helpers import (
    build_product_mutation_payload,
    get_product_match,
    run_product_import_update,
)


class ActivateProductMcpTool(BaseMcpTool):
    name = "activate_product"
    title = "Activate Product"
    output_schema = PRODUCT_MUTATION_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Activate a product by exact product ID or exact SKU."""
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            await ctx.info(
                f"Activating product for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sanitized_sku!r}."
            )
            response_data = await self._activate_product(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
            )
            return self.build_result(
                summary=f"Activated product '{response_data['product']['name']}' ({response_data['product']['sku']}).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Activate product failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @database_sync_to_async
    def _activate_product(self, *, multi_tenant_company, product_id: int | None, sku: str | None) -> ProductMutationPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            run_product_import_update(
                multi_tenant_company=multi_tenant_company,
                product=product,
                product_data={"active": True},
            )
            return build_product_mutation_payload(
                multi_tenant_company=multi_tenant_company,
                product=product,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
