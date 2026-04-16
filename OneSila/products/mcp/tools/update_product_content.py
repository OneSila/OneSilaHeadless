from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CONTENT, TAG_EDIT, TAG_PRODUCTS, tool_tags
from products.mcp.output_types import PRODUCT_MUTATION_OUTPUT_SCHEMA
from products.mcp.types import ProductMutationPayload
from products.mcp.update_helpers import (
    build_product_mutation_payload,
    get_existing_translation_seed,
    get_product_match,
    get_sales_channel_match,
    run_product_import_update,
    sanitize_bullet_points_input,
    validate_company_language,
)


class UpdateProductContentMcpTool(BaseMcpTool):
    name = "update_product_content"
    title = "Update Product Content"
    tags = tool_tags(TAG_EDIT, TAG_PRODUCTS, TAG_CONTENT)
    output_schema = PRODUCT_MUTATION_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        language: Annotated[str, Field(description="Target company language code for the translation update.")] = ...,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID. Requires either product_id or sku.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU. Requires either product_id or sku.")] = None,
        sales_channel_id: Annotated[int | None, Field(ge=1, description="Optional exact sales channel database ID for a channel-specific translation override. Use search_sales_channels first to map hostnames or marketplace names to ids.")] = None,
        name: Annotated[str | None, Field(description="Updated product name for the target translation.")] = None,
        subtitle: Annotated[str | None, Field(description="Updated subtitle for the target translation.")] = None,
        short_description: Annotated[str | None, Field(description="Updated short description for the target translation.")] = None,
        description: Annotated[str | None, Field(description="Updated long description for the target translation.")] = None,
        bullet_points: Annotated[
            list[str] | str | None,
            Field(description="Optional list of bullet points for the target translation. A JSON-stringified list is also accepted.")
        ] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Update one product translation target, either the global translation or one sales-channel-specific override.
        This tool persists content provided by the caller; content generation should happen in the chat before calling it.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_language = validate_company_language(
                language=language,
                multi_tenant_company=multi_tenant_company,
            )
            sanitized_bullet_points = self._sanitize_bullet_points(bullet_points=bullet_points)
            self._validate_update_request(
                name=name,
                subtitle=subtitle,
                short_description=short_description,
                description=description,
                bullet_points=sanitized_bullet_points,
            )
            await ctx.info(
                f"Updating product content for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sanitized_sku!r}, language={sanitized_language!r}, "
                f"sales_channel_id={sales_channel_id!r}."
            )
            response_data = await self._update_product_content(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
                language=sanitized_language,
                sales_channel_id=sales_channel_id,
                name=name,
                subtitle=subtitle,
                short_description=short_description,
                description=description,
                bullet_points=sanitized_bullet_points,
            )
            return self.build_result(
                summary=(
                    f"Updated content for product '{response_data['name']}' "
                    f"({response_data['sku']}) in language {sanitized_language}."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Update product content failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_bullet_points(self, *, bullet_points: list[str] | str | None) -> list[str] | None:
        try:
            return sanitize_bullet_points_input(bullet_points=bullet_points)
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _validate_update_request(
        self,
        *,
        name: str | None,
        subtitle: str | None,
        short_description: str | None,
        description: str | None,
        bullet_points: list[str] | None,
    ) -> None:
        if not any(
            [
                name is not None,
                subtitle is not None,
                short_description is not None,
                description is not None,
                bullet_points is not None,
            ]
        ):
            raise McpToolError(
                "Provide at least one content field: name, subtitle, short_description, description, or bullet_points."
            )

    @database_sync_to_async
    def _update_product_content(
        self,
        *,
        multi_tenant_company,
        product_id: int | None,
        sku: str | None,
        language: str,
        sales_channel_id: int | None,
        name: str | None,
        subtitle: str | None,
        short_description: str | None,
        description: str | None,
        bullet_points: list[str] | None,
    ) -> ProductMutationPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            sales_channel = get_sales_channel_match(
                multi_tenant_company=multi_tenant_company,
                sales_channel_id=sales_channel_id,
            )
            seed_data = get_existing_translation_seed(
                product=product,
                language=language,
                sales_channel=sales_channel,
            )
            translation_payload = {
                "language": language,
                "name": name if name is not None else seed_data["name"],
            }
            if subtitle is not None:
                translation_payload["subtitle"] = subtitle
            if short_description is not None:
                translation_payload["short_description"] = short_description
            if description is not None:
                translation_payload["description"] = description
            if bullet_points is not None:
                translation_payload["bullet_points"] = bullet_points

            run_product_import_update(
                multi_tenant_company=multi_tenant_company,
                product=product,
                product_data={"translations": [translation_payload]},
                sales_channel=sales_channel,
            )
            return build_product_mutation_payload(
                product=product,
                action=f"content update for language {language}",
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
