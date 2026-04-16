from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_EDIT, TAG_IMAGES, TAG_PRODUCTS, tool_tags
from products.mcp.output_types import PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA
from products.mcp.types import ProductBatchMutationPayload, ProductImageInputPayload
from products.mcp.update_helpers import (
    build_product_batch_mutation_payload,
    get_product_match,
    get_sales_channel_match,
    group_images_by_sales_channel_id,
    run_product_import_update,
    sanitize_product_images_input,
)


class AddProductImagesMcpTool(BaseMcpTool):
    name = "add_product_images"
    title = "Add Product Images"
    tags = tool_tags(TAG_EDIT, TAG_PRODUCTS, TAG_IMAGES)
    output_schema = PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": True,
    }

    async def execute(
        self,
        images: Annotated[
            list[ProductImageInputPayload] | str,
            Field(
                description=(
                    "Non-empty list of image inputs. Each image must include image_url and may include title, "
                    "description, type, is_main_image, sort_order, and sales_channel_id. "
                    "Use search_sales_channels first to map hostnames or marketplace names to sales_channel_id. "
                    "A JSON-stringified list is also accepted."
                )
            )
        ] = ...,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID. Requires either product_id or sku.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU. Requires either product_id or sku.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """Add one or more images to an existing product, optionally targeting channel-specific assignments. Requires either `product_id` or `sku`."""
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_images = self._sanitize_images(images=images)
            await ctx.info(
                f"Adding product images for company_id={multi_tenant_company.id} "
                f"with product_id={product_id!r}, sku={sanitized_sku!r}, images={len(sanitized_images)}."
            )
            response_data = await self._add_product_images(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
                images=sanitized_images,
            )
            return self.build_result(
                summary=(
                    f"Processed {response_data['updated_count']} image assignment(s) for "
                    f"'{response_data['name']}' ({response_data['sku']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Add product images failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_images(self, *, images: list[ProductImageInputPayload] | str) -> list[ProductImageInputPayload]:
        try:
            return sanitize_product_images_input(images=images)
        except ValueError as error:
            raise McpToolError(str(error)) from error

    @database_sync_to_async
    def _add_product_images(
        self,
        *,
        multi_tenant_company,
        product_id: int | None,
        sku: str | None,
        images: list[ProductImageInputPayload],
    ) -> ProductBatchMutationPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            grouped_images = group_images_by_sales_channel_id(images=images)
            updated_count = 0
            for sales_channel_id, grouped_payload in grouped_images.items():
                sales_channel = get_sales_channel_match(
                    multi_tenant_company=multi_tenant_company,
                    sales_channel_id=sales_channel_id,
                )
                import_instance = run_product_import_update(
                    multi_tenant_company=multi_tenant_company,
                    product=product,
                    product_data={"images": grouped_payload},
                    sales_channel=sales_channel,
                )
                updated_count += import_instance.images_associations_instances.count()

            return build_product_batch_mutation_payload(
                product=product,
                updated_count=updated_count,
                action="image update",
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
