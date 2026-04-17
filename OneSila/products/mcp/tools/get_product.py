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
from products.mcp.helpers import get_product_detail_queryset, serialize_product_detail
from products.mcp.output_types import GET_PRODUCT_OUTPUT_SCHEMA
from products.mcp.types import ProductDetailPayload
from products.models import Product


class GetProductMcpTool(BaseMcpTool):
    name = "get_product"
    title = "Get Product"
    read_only = True
    tags = tool_tags(TAG_GET, TAG_PRODUCTS)
    output_schema = GET_PRODUCT_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        sku: Annotated[str, Field(description="Exact SKU for the product within the authenticated company.")] ,
        show_inspector: Annotated[
            bool,
            Field(
                description=(
                    "Include product data-quality and readiness inspector status and issue blocks. "
                    "Use this when checking what information is missing or why the product is not ready."
                )
            ),
        ] = False,
        show_website_views_assign: Annotated[
            bool,
            Field(
                description=(
                    "Include website-view assignments for this product. "
                    "Use this when checking which storefront views the product is assigned to "
                    "and which remote product URLs already exist there."
                )
            ),
        ] = False,
        show_property_requirements: Annotated[
            bool,
            Field(
                description=(
                    "Include the expected property map for the current product type. "
                    "This can be large. Use it when inspector issues do not show which properties are missing, "
                    "or when you need the full required and optional property list."
                )
            ),
        ] = False,
        show_translations: Annotated[
            bool,
            Field(
                description="Include product translations. Use this when editing or creating translations."
            ),
        ] = False,
        show_vat_rate_data: Annotated[
            bool,
            Field(description="Include detailed VAT rate data in addition to the top-level vat_rate percentage."),
        ] = False,
        show_images: Annotated[
            bool,
            Field(description="Include assigned product images. Each image entry returns image_url, thumbnail_url, type, title, description, is_main_image, sort_order, and optional sales_channel."),
        ] = False,
        show_properties: Annotated[
            bool,
            Field(description="Include assigned product properties and values."),
        ] = False,
        show_prices: Annotated[
            bool,
            Field(description="Include product prices."),
        ] = False,
        show_brand_voice: Annotated[
            bool,
            Field(
                description=(
                    "Include brand voice guidance resolved for this product's assigned brand. "
                    "Use this when drafting or translating product content so the copy follows the brand style."
                )
            ),
        ] = False,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get one product by exact SKU for the authenticated company.

        This is the main product-inspection and product-editing read tool. The default response is
        intentionally small so the caller only pays for the fields needed for the current step.

        Use the show_* flags carefully:
        - show_inspector: when checking data quality, missing information, or why the product is not ready.
        - show_website_views_assign: when checking which website/storefront views the product is assigned to and their remote URLs.
        - show_property_requirements: when the inspector is not enough and you need the full required or optional property map.
        - show_translations: when reviewing, creating, or updating translated product content.
        - show_vat_rate_data: when the VAT configuration details are needed, not just the top-level rate.
        - show_images: when reviewing or updating assigned product images. This is the exact runtime image shape used by create_products and upsert_products.
        - show_properties: when reviewing or updating assigned property values.
        - show_prices: when reviewing or updating product prices.
        - show_brand_voice: when writing or translating content and the copy should follow the product brand style.

        Prefer enabling only the sections needed for the current task.
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
                show_inspector=self.sanitize_optional_bool(value=show_inspector, field_name="show_inspector") or False,
                show_website_views_assign=self.sanitize_optional_bool(
                    value=show_website_views_assign,
                    field_name="show_website_views_assign",
                ) or False,
                show_property_requirements=self.sanitize_optional_bool(
                    value=show_property_requirements,
                    field_name="show_property_requirements",
                ) or False,
                show_translations=self.sanitize_optional_bool(
                    value=show_translations,
                    field_name="show_translations",
                ) or False,
                show_vat_rate_data=self.sanitize_optional_bool(
                    value=show_vat_rate_data,
                    field_name="show_vat_rate_data",
                ) or False,
                show_images=self.sanitize_optional_bool(
                    value=show_images,
                    field_name="show_images",
                ) or False,
                show_properties=self.sanitize_optional_bool(
                    value=show_properties,
                    field_name="show_properties",
                ) or False,
                show_prices=self.sanitize_optional_bool(
                    value=show_prices,
                    field_name="show_prices",
                ) or False,
                show_brand_voice=self.sanitize_optional_bool(
                    value=show_brand_voice,
                    field_name="show_brand_voice",
                ) or False,
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
        show_inspector: bool,
        show_website_views_assign: bool,
        show_property_requirements: bool,
        show_translations: bool,
        show_vat_rate_data: bool,
        show_images: bool,
        show_properties: bool,
        show_prices: bool,
        show_brand_voice: bool,
    ) -> ProductDetailPayload:
        try:
            product = get_product_detail_queryset(
                multi_tenant_company=multi_tenant_company,
            ).get(sku=sku)
        except Product.DoesNotExist as error:
            raise McpToolError("Product not found.") from error

        return serialize_product_detail(
            product=product,
            show_inspector=show_inspector,
            show_website_views_assign=show_website_views_assign,
            show_property_requirements=show_property_requirements,
            show_translations=show_translations,
            show_vat_rate_data=show_vat_rate_data,
            show_images=show_images,
            show_properties=show_properties,
            show_prices=show_prices,
            show_brand_voice=show_brand_voice,
        )
