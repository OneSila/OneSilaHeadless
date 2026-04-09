from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_GET, TAG_PRODUCTS, tool_tags
from products.mcp.helpers import serialize_product_onesila_url
from products.mcp.output_types import GET_PRODUCT_ONESILA_URL_OUTPUT_SCHEMA
from products.mcp.types import ProductOnesilaUrlPayload
from products.models import Product


class GetProductOnesilaUrlMcpTool(BaseMcpTool):
    name = "get_product_onesila_url"
    title = "Get Product OneSila URL"
    read_only = True
    tags = tool_tags(TAG_GET, TAG_PRODUCTS)
    output_schema = GET_PRODUCT_ONESILA_URL_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        sku: Annotated[str | None, Field(description="Exact SKU for the product within the authenticated company.")] = None,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get the OneSila URL for a single company-scoped product.
        This returns the product global id, the OneSila path, and the absolute OneSila URL
        using the existing `/products/product/{global_id}` route pattern.

        Args:
            sku: Exact product SKU.
            product_id: Exact product database ID.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            if product_id is None and not sku:
                raise McpToolError("Provide product_id or sku.")

            if sku is not None:
                sku = self.validate_required_string(value=sku, field_name="sku")

            await ctx.info(
                f"Getting product OneSila URL for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sku!r}."
            )
            response_data = await self._get_product_onesila_url(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            await ctx.info(
                f"Resolved OneSila path for product_id={response_data['id']} sku={response_data['sku']!r}."
            )
            return self.build_result(
                summary=f"OneSila URL for product '{response_data['sku']}' is {response_data['onesila_path']}.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get product OneSila URL failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_product_onesila_url(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        product_id: int | None,
        sku: str | None,
    ) -> ProductOnesilaUrlPayload:
        queryset = Product.objects.filter(multi_tenant_company=multi_tenant_company)

        if product_id is not None:
            queryset = queryset.filter(id=product_id)
        if sku:
            queryset = queryset.filter(sku=sku)

        product_ids = list(queryset.order_by("id").values_list("id", flat=True).distinct()[:2])
        if not product_ids:
            raise McpToolError("Product not found.")
        if len(product_ids) > 1:
            raise McpToolError("Multiple products matched the provided identifiers.")

        product = queryset.get(id=product_ids[0])
        return serialize_product_onesila_url(product=product)
