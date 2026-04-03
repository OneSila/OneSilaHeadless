from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from products.mcp.helpers import get_product_detail_queryset, serialize_product_detail
from products.mcp.output_types import GET_PRODUCT_OUTPUT_SCHEMA
from products.mcp.types import ProductDetailPayload
from products.models import Product


class GetProductMcpTool(BaseMcpTool):
    name = "get_product"
    title = "Get Product"
    read_only = True
    output_schema = GET_PRODUCT_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        sku: Annotated[str, Field(description="Exact SKU for the product within the authenticated company.")] ,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get a single company-scoped product by exact SKU.
        Use this when you already know the SKU and need the product detail, pricing,
        assigned property values, images, VAT data, and inspector status.

        Args:
            sku: Exact product SKU.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sku = self.validate_required_string(value=sku, field_name="sku")
            await ctx.info(
                f"Getting product for company_id={multi_tenant_company.id} with sku={sku!r}."
            )
            response_data = await self._get_product_detail(
                multi_tenant_company=multi_tenant_company,
                sku=sku,
            )
            await ctx.info(
                f"Loaded product_id={response_data['id']} sku={response_data['sku']!r}."
            )
            return self.build_result(
                summary=f"Loaded product '{response_data['name']}' ({response_data['sku']}).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get product failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_product_detail(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        sku: str,
    ) -> ProductDetailPayload:
        try:
            product = get_product_detail_queryset(
                multi_tenant_company=multi_tenant_company,
            ).get(sku=sku)
        except Product.DoesNotExist as error:
            raise McpToolError("Product not found.") from error

        return serialize_product_detail(product=product)
