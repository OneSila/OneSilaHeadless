from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from products.mcp.output_types import PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA
from products.mcp.types import ProductBatchMutationPayload, ProductPropertyValueUpdateInputPayload
from products.mcp.update_helpers import (
    build_product_batch_mutation_payload,
    get_product_match,
    resolve_properties_for_updates,
    run_product_import_update,
    sanitize_product_property_updates_input,
)


class UpsertProductPropertyValuesMcpTool(BaseMcpTool):
    name = "upsert_product_property_values"
    title = "Upsert Product Property Values"
    output_schema = PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        updates: Annotated[
            list[ProductPropertyValueUpdateInputPayload] | str,
            Field(
                description=(
                    "Non-empty list of property value updates. Each update must include property_id or "
                    "property_internal_name, plus value. For SELECT and MULTISELECT, prefer select-value IDs "
                    "with value_is_id=true. For TEXT and DESCRIPTION, translations may also be provided. "
                    "A JSON-stringified list is also accepted."
                )
            )
        ] = ...,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Upsert one or more product property values on an existing product."""
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_updates = self._sanitize_updates(
                updates=updates,
                multi_tenant_company=multi_tenant_company,
            )
            await ctx.info(
                f"Upserting product property values for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sanitized_sku!r}, updates={len(sanitized_updates)}."
            )
            response_data = await self._upsert_product_property_values(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
                updates=sanitized_updates,
            )
            return self.build_result(
                summary=(
                    f"Upserted {response_data['updated_count']} product property value(s) for "
                    f"'{response_data['product']['name']}' ({response_data['product']['sku']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Upsert product property values failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _sanitize_updates(
        self,
        *,
        updates: list[ProductPropertyValueUpdateInputPayload] | str,
        multi_tenant_company,
    ) -> list[ProductPropertyValueUpdateInputPayload]:
        try:
            return sanitize_product_property_updates_input(
                updates=updates,
                multi_tenant_company=multi_tenant_company,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error

    @database_sync_to_async
    def _upsert_product_property_values(
        self,
        *,
        multi_tenant_company,
        product_id: int | None,
        sku: str | None,
        updates: list[ProductPropertyValueUpdateInputPayload],
    ) -> ProductBatchMutationPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            resolved_updates = resolve_properties_for_updates(
                multi_tenant_company=multi_tenant_company,
                updates=updates,
            )
            import_instance = run_product_import_update(
                multi_tenant_company=multi_tenant_company,
                product=product,
                product_data={"properties": resolved_updates},
            )
            return build_product_batch_mutation_payload(
                multi_tenant_company=multi_tenant_company,
                product=product,
                updated_count=import_instance.product_property_instances.count(),
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
