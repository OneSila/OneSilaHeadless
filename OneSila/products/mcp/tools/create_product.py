from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CREATE, TAG_PRODUCTS, tool_tags
from products.mcp.create_helpers import (
    build_create_product_data,
    build_create_product_payload,
    run_product_create,
)
from products.mcp.output_types import CREATE_PRODUCT_OUTPUT_SCHEMA
from products.mcp.types import CreateProductPayload, ProductTypeValue


class CreateProductMcpTool(BaseMcpTool):
    name = "create_product"
    title = "Create Product"
    tags = tool_tags(TAG_CREATE, TAG_PRODUCTS)
    output_schema = CREATE_PRODUCT_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        type: Annotated[ProductTypeValue, Field(description="Required structural product type, for example SIMPLE or CONFIGURABLE.")] = ...,
        name: Annotated[str, Field(description="Required default product name.")] = ...,
        sku: Annotated[str | None, Field(description="Optional custom SKU. If omitted, the system generates one automatically.")] = None,
        product_type_id: Annotated[int | None, Field(ge=1, description="Recommended exact product-type select-value database ID from get_product_types.")] = None,
        product_type_value: Annotated[str | None, Field(description="Fallback exact product-type value text when product_type_id is not available.")] = None,
        price: Annotated[str | float | int | None, Field(description="Recommended default price. If provided, it is stored in the company's default currency.")] = None,
        rrp: Annotated[str | float | int | None, Field(description="Optional recommended retail price. Ignored when not provided.")] = None,
        vat_rate_id: Annotated[int | None, Field(ge=1, description="Recommended exact VAT rate database ID from get_vat_rates.")] = None,
        vat_rate: Annotated[int | None, Field(ge=0, description="Fallback exact VAT percentage when vat_rate_id is not available.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create a minimal product for the authenticated company.
        Required fields are only `type` and `name`. When available, prefer using get_product_types first
        and pass product_type_id, and use get_vat_rates first and pass vat_rate_id. If price or rrp is provided,
        the tool stores it in the company's default currency.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_name = self.validate_required_string(value=name, field_name="name")
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_product_type_value = self._sanitize_optional_string(value=product_type_value)

            await ctx.info(
                f"Creating product for company_id={multi_tenant_company.id} with type={type!r}, "
                f"name={sanitized_name!r}, sku={sanitized_sku!r}, product_type_id={product_type_id!r}, "
                f"vat_rate_id={vat_rate_id!r}."
            )
            response_data = await self._create_product(
                multi_tenant_company=multi_tenant_company,
                product_type_code=type,
                name=sanitized_name,
                sku=sanitized_sku,
                product_type_id=product_type_id,
                product_type_value=sanitized_product_type_value,
                price=price,
                rrp=rrp,
                vat_rate_id=vat_rate_id,
                vat_rate=vat_rate,
            )
            return self.build_result(
                summary=(
                    f"Created product '{response_data['product']['name']}' "
                    f"({response_data['product']['sku']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create product failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @database_sync_to_async
    def _create_product(
        self,
        *,
        multi_tenant_company,
        product_type_code: ProductTypeValue,
        name: str,
        sku: str | None,
        product_type_id: int | None,
        product_type_value: str | None,
        price,
        rrp,
        vat_rate_id: int | None,
        vat_rate: int | None,
    ) -> CreateProductPayload:
        try:
            product_data, sku_was_generated = build_create_product_data(
                multi_tenant_company=multi_tenant_company,
                name=name,
                product_type_code=product_type_code,
                sku=sku,
                product_type_id=product_type_id,
                product_type_value=product_type_value,
                price=price,
                rrp=rrp,
                vat_rate_id=vat_rate_id,
                vat_rate=vat_rate,
            )
            import_instance = run_product_create(
                multi_tenant_company=multi_tenant_company,
                product_data=product_data,
            )
            if not import_instance.created:
                if sku:
                    raise ValueError(f"Product with sku {sku!r} already exists.")
                raise ValueError("Product was not created.")

            return build_create_product_payload(
                multi_tenant_company=multi_tenant_company,
                product=import_instance.instance,
                sku_was_generated=sku_was_generated,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
