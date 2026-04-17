from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CONTENT, TAG_EDIT, TAG_IMAGES, TAG_PRICES, TAG_PRODUCTS, TAG_PROPERTIES, tool_tags
from products.mcp.output_types import PRODUCT_UPSERT_OUTPUT_SCHEMA
from products.mcp.types import (
    ProductImageInputPayload,
    ProductPriceUpsertInputPayload,
    ProductPropertyValueUpdateInputPayload,
    ProductTranslationUpsertInputPayload,
    ProductUpsertPayload,
)
from products.mcp.update_helpers import (
    get_product_match,
    run_upsert_product_updates,
    sanitize_product_images_input,
    sanitize_product_prices_input,
    sanitize_product_property_updates_input,
    sanitize_product_translation_updates_input,
)


class UpsertProductMcpTool(BaseMcpTool):
    name = "upsert_product"
    title = "Upsert Product"
    tags = tool_tags(TAG_EDIT, TAG_PRODUCTS, TAG_CONTENT, TAG_PRICES, TAG_PROPERTIES, TAG_IMAGES)
    output_schema = PRODUCT_UPSERT_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        product_id: Annotated[int | None, Field(ge=1, description="Exact product database ID. Requires either product_id or sku.")] = None,
        sku: Annotated[str | None, Field(description="Exact product SKU. Requires either product_id or sku.")] = None,
        active: Annotated[
            bool | None,
            Field(description="Set product active status. true activates, false deactivates. Omit to leave unchanged."),
        ] = None,
        ean_code: Annotated[
            str | None,
            Field(
                description=(
                    "Optional EAN code to assign to the product. Only include this when the user explicitly wants to "
                    "set or change the product EAN code. Omit to leave the current EAN unchanged."
                )
            ),
        ] = None,
        translations: Annotated[
            list[ProductTranslationUpsertInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of translation updates. Use this for content changes such as name, subtitle, "
                    "short_description, description, and bullet_points. Each entry must include language and may "
                    "optionally include sales_channel_id for a channel-specific override. Omit to leave translations unchanged. "
                    "A JSON-stringified list is also accepted."
                )
            ),
        ] = None,
        prices: Annotated[
            list[ProductPriceUpsertInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of price updates. Each entry must include currency and price, and may include rrp. "
                    "Use get_company_details with show_currencies=true when you need the allowed company currencies. "
                    "Omit to leave prices unchanged. A JSON-stringified list is also accepted."
                )
            ),
        ] = None,
        properties: Annotated[
            list[ProductPropertyValueUpdateInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of property value updates. Each entry must include property_id or "
                    "property_internal_name, plus value. For SELECT and MULTISELECT, prefer select-value IDs with "
                    "value_is_id=true. Omit to leave properties unchanged. A JSON-stringified list is also accepted."
                )
            ),
        ] = None,
        images: Annotated[
            list[ProductImageInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of image assignments to add. Each image must include image_url and may include "
                    "title, description, type, is_main_image, sort_order, and sales_channel_id. "
                    "Use search_sales_channels first when you need to map a website or marketplace to sales_channel_id. "
                    "Omit to leave images unchanged. A JSON-stringified list is also accepted."
                )
            ),
        ] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create one or more updates on an existing product in a single call.

        This is the main product write tool. Use it when a product needs one or more updates together,
        such as active status, EAN code, translations, prices, properties, or images.

        Use this tool to reduce repeated write calls:
        - set active=true or active=false to activate or deactivate the product
        - set ean_code to assign or change the product EAN code
        - use translations to create or update product content
        - use prices to create or update one or more currency prices
        - use properties to create or update assigned property values
        - use images to add one or more product images

        Rules:
        - Requires either product_id or sku.
        - Include only the sections you want to change.
        - At least one update section must be provided.
        - The call is atomic: if one part is invalid, the whole update fails.
        - For translation work, use get_product(show_translations=true) first if you need the current translations.
        - For content writing or translation, use get_product(show_brand_voice=true) if brand voice guidance may matter.
        - For allowed company languages, currencies, or product types, use get_company_details first.
        - For product data quality or missing-information checks, use get_product(show_inspector=true).

        Do not send unchanged sections just because they exist. Keep the request limited to the fields
        the user actually wants to modify.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_sku = self._sanitize_optional_string(value=sku)
            sanitized_active = self.sanitize_optional_bool(value=active, field_name="active")
            sanitized_ean_code = self._sanitize_optional_string(value=ean_code)
            sanitized_translations = self._sanitize_translations(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )
            sanitized_prices = self._sanitize_prices(prices=prices)
            sanitized_properties = self._sanitize_properties(
                properties=properties,
                multi_tenant_company=multi_tenant_company,
            )
            sanitized_images = self._sanitize_images(images=images)
            self._validate_has_updates(
                active=sanitized_active,
                ean_code=sanitized_ean_code,
                translations=sanitized_translations,
                prices=sanitized_prices,
                properties=sanitized_properties,
                images=sanitized_images,
            )
            requested_sections = {
                "active": sanitized_active,
                "ean_code": sanitized_ean_code,
                "translations": sanitized_translations,
                "prices": sanitized_prices,
                "properties": sanitized_properties,
                "images": sanitized_images,
            }
            await ctx.info(
                f"Upserting product for company_id={multi_tenant_company.id} with "
                f"product_id={product_id!r}, sku={sanitized_sku!r}, "
                f"sections={[key for key, value in requested_sections.items() if value is not None]}."
            )
            response_data = await self._upsert_product(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sanitized_sku,
                active=sanitized_active,
                ean_code=sanitized_ean_code,
                translations=sanitized_translations,
                prices=sanitized_prices,
                properties=sanitized_properties,
                images=sanitized_images,
            )
            return self.build_result(
                summary=f"Updated product '{response_data['name']}' ({response_data['sku']}).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Upsert product failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_translations(
        self,
        *,
        translations: list[ProductTranslationUpsertInputPayload] | str | None,
        multi_tenant_company,
    ) -> list[ProductTranslationUpsertInputPayload] | None:
        try:
            return sanitize_product_translation_updates_input(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _sanitize_prices(
        self,
        *,
        prices: list[ProductPriceUpsertInputPayload] | str | None,
    ) -> list[ProductPriceUpsertInputPayload] | None:
        try:
            return sanitize_product_prices_input(prices=prices)
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _sanitize_properties(
        self,
        *,
        properties: list[ProductPropertyValueUpdateInputPayload] | str | None,
        multi_tenant_company,
    ) -> list[ProductPropertyValueUpdateInputPayload] | None:
        if properties is None:
            return None
        try:
            return sanitize_product_property_updates_input(
                updates=properties,
                multi_tenant_company=multi_tenant_company,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _sanitize_images(
        self,
        *,
        images: list[ProductImageInputPayload] | str | None,
    ) -> list[ProductImageInputPayload] | None:
        if images is None:
            return None
        try:
            return sanitize_product_images_input(images=images)
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _validate_has_updates(
        self,
        *,
        active: bool | None,
        ean_code: str | None,
        translations: list[ProductTranslationUpsertInputPayload] | None,
        prices: list[ProductPriceUpsertInputPayload] | None,
        properties: list[ProductPropertyValueUpdateInputPayload] | None,
        images: list[ProductImageInputPayload] | None,
    ) -> None:
        if not any(
            [
                active is not None,
                ean_code is not None,
                translations is not None,
                prices is not None,
                properties is not None,
                images is not None,
            ]
        ):
            raise McpToolError(
                "Provide at least one update section: active, ean_code, translations, prices, properties, or images."
            )

    @database_sync_to_async
    def _upsert_product(
        self,
        *,
        multi_tenant_company,
        product_id: int | None,
        sku: str | None,
        active: bool | None,
        ean_code: str | None,
        translations: list[ProductTranslationUpsertInputPayload] | None,
        prices: list[ProductPriceUpsertInputPayload] | None,
        properties: list[ProductPropertyValueUpdateInputPayload] | None,
        images: list[ProductImageInputPayload] | None,
    ) -> ProductUpsertPayload:
        try:
            product = get_product_match(
                multi_tenant_company=multi_tenant_company,
                product_id=product_id,
                sku=sku,
            )
            return run_upsert_product_updates(
                multi_tenant_company=multi_tenant_company,
                product=product,
                active=active,
                ean_code=ean_code,
                translations=translations,
                prices=prices,
                properties=properties,
                images=images,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error
