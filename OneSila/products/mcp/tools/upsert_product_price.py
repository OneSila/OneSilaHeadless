from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_EDIT, TAG_PRICES, TAG_PRODUCTS, tool_tags
from products.mcp.output_types import PRODUCT_MUTATION_OUTPUT_SCHEMA
from products.mcp.types import ProductMutationPayload
from products.mcp.update_helpers import (
    build_product_mutation_payload,
    get_product_match,
    run_product_import_update,
)


class UpsertProductPriceMcpTool(BaseMcpTool):
    name = "upsert_product_price"
    title = "Upsert Product Price"
    tags = tool_tags(TAG_EDIT, TAG_PRODUCTS, TAG_PRICES)
    output_schema = PRODUCT_MUTATION_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        currency: Annotated[str, Field(description="Currency ISO code, for example EUR or GBP.")] = ...,
        price: Annotated[str | float | int, Field(description="Net sale price or effective product price.")] = ...,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU.")] = None,
        rrp: Annotated[str | float | int | None, Field(description="Optional recommended retail price.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create or update the price for a single product and currency.
        This uses the existing product import factory with only the `prices` key populated.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_currency = self.validate_required_string(value=currency, field_name="currency").upper()
            await ctx.info(
                f"Upserting product price for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sanitized_sku!r}, currency={sanitized_currency!r}."
            )
            response_data = await self._upsert_product_price(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
                currency=sanitized_currency,
                price=price,
                rrp=rrp,
            )
            return self.build_result(
                summary=(
                    f"Upserted {sanitized_currency} price for product "
                    f"'{response_data['product']['name']}' ({response_data['product']['sku']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Upsert product price failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @database_sync_to_async
    def _upsert_product_price(
        self,
        *,
        multi_tenant_company,
        product_id: int | None,
        sku: str | None,
        currency: str,
        price,
        rrp,
    ) -> ProductMutationPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            run_product_import_update(
                multi_tenant_company=multi_tenant_company,
                product=product,
                product_data={
                    "prices": [
                        {
                            "currency": currency,
                            "price": price,
                            "rrp": rrp,
                        }
                    ]
                },
            )
            return build_product_mutation_payload(
                multi_tenant_company=multi_tenant_company,
                product=product,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
