from __future__ import annotations

from typing import Annotated, Any

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CONTENT, TAG_EDIT, TAG_IMAGES, TAG_PRICES, TAG_PRODUCTS, TAG_PROPERTIES, tool_tags
from llm.models import McpToolRun
from products.mcp.output_types import UPSERT_PRODUCTS_OUTPUT_SCHEMA
from products.mcp.types import (
    ProductImageInputPayload,
    ProductPriceUpsertInputPayload,
    ProductPropertyValueUpdateInputPayload,
    ProductTranslationUpsertInputPayload,
    UpsertProductInputPayload,
    UpsertProductsPayload,
)
from products.mcp.update_helpers import (
    get_product_match,
    run_upsert_product_updates,
    sanitize_product_images_input,
    sanitize_product_prices_input,
    sanitize_product_property_updates_input,
    sanitize_sales_channel_view_ids_input,
    sanitize_product_translation_updates_input,
)


class UpsertProductsMcpTool(BaseMcpTool):
    name = "upsert_products"
    title = "Upsert Products"
    tags = tool_tags(TAG_EDIT, TAG_PRODUCTS, TAG_CONTENT, TAG_PRICES, TAG_PROPERTIES, TAG_IMAGES)
    output_schema = UPSERT_PRODUCTS_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 10

    async def execute(
        self,
        products: Annotated[
            list[UpsertProductInputPayload] | UpsertProductInputPayload | str,
            Field(
                description=(
                    "One product update object or an array of product update objects. "
                    "This tool supports updating up to 10 products per call. "
                    "Use a single object for one product or an array for bulk updates. "
                    "Each item can update active status, EAN, translations, prices, properties, images, "
                    "and sales_channel_view_ids."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Update one or more existing products in a single call.

        Pass `products` as either a single object or an array of objects. A single object is normalized
        to a one-item batch, and the response always returns an array in `results`.

        Limits:
        - up to 10 products per call

        Use this when one or more products need coordinated updates such as active status, EAN code,
        translations, prices, properties, images, or website/storefront assignments.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            raw_items = self.normalize_bulk_input(
                value=products,
                field_name="products",
                maximum=self.maximum_items,
            )
            sanitized_products = [
                self._sanitize_product_item(
                    product=item,
                    multi_tenant_company=multi_tenant_company,
                )
                for item in raw_items
            ]
            await ctx.info(
                f"Upserting {len(sanitized_products)} product(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"products": sanitized_products},
                total_records=len(sanitized_products),
                update_only=True,
            )
            response_data = await self._upsert_products(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                products=sanitized_products,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} product update request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Upsert products failed: {error}")
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

    def _sanitize_sales_channel_view_ids(
        self,
        *,
        sales_channel_view_ids,
    ) -> list[int] | None:
        try:
            return sanitize_sales_channel_view_ids_input(
                sales_channel_view_ids=sales_channel_view_ids,
            )
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
        sales_channel_view_ids: list[int] | None,
    ) -> None:
        if not any(
            [
                active is not None,
                ean_code is not None,
                translations is not None,
                prices is not None,
                properties is not None,
                images is not None,
                sales_channel_view_ids is not None,
            ]
        ):
            raise McpToolError(
                "Each product update must include at least one section: active, ean_code, translations, prices, properties, images, or sales_channel_view_ids."
            )

    def _sanitize_product_item(
        self,
        *,
        product: dict[str, Any],
        multi_tenant_company,
    ) -> UpsertProductInputPayload:
        sanitized_product: UpsertProductInputPayload = {}

        sanitized_product_id = self.sanitize_optional_int(
            value=product.get("product_id"),
            field_name="product_id",
            minimum=1,
        )
        sanitized_sku = self._sanitize_optional_string(value=product.get("sku"))
        if sanitized_product_id is None and not sanitized_sku:
            raise McpToolError("Each product update must provide product_id or sku.")

        sanitized_active = self.sanitize_optional_bool(value=product.get("active"), field_name="active")
        sanitized_ean_code = self._sanitize_optional_string(value=product.get("ean_code"))
        sanitized_translations = self._sanitize_translations(
            translations=product.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )
        sanitized_prices = self._sanitize_prices(prices=product.get("prices"))
        sanitized_properties = self._sanitize_properties(
            properties=product.get("properties"),
            multi_tenant_company=multi_tenant_company,
        )
        sanitized_images = self._sanitize_images(images=product.get("images"))
        sanitized_sales_channel_view_ids = self._sanitize_sales_channel_view_ids(
            sales_channel_view_ids=product.get("sales_channel_view_ids"),
        )

        self._validate_has_updates(
            active=sanitized_active,
            ean_code=sanitized_ean_code,
            translations=sanitized_translations,
            prices=sanitized_prices,
            properties=sanitized_properties,
            images=sanitized_images,
            sales_channel_view_ids=sanitized_sales_channel_view_ids,
        )

        if sanitized_product_id is not None:
            sanitized_product["product_id"] = sanitized_product_id
        if sanitized_sku:
            sanitized_product["sku"] = sanitized_sku
        if sanitized_active is not None:
            sanitized_product["active"] = sanitized_active
        if sanitized_ean_code:
            sanitized_product["ean_code"] = sanitized_ean_code
        if sanitized_translations is not None:
            sanitized_product["translations"] = sanitized_translations
        if sanitized_prices is not None:
            sanitized_product["prices"] = sanitized_prices
        if sanitized_properties is not None:
            sanitized_product["properties"] = sanitized_properties
        if sanitized_images is not None:
            sanitized_product["images"] = sanitized_images
        if sanitized_sales_channel_view_ids is not None:
            sanitized_product["sales_channel_view_ids"] = sanitized_sales_channel_view_ids

        return sanitized_product

    @database_sync_to_async
    def _upsert_products(
        self,
        *,
        multi_tenant_company,
        tool_run_id: int,
        products: list[UpsertProductInputPayload],
    ) -> UpsertProductsPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []
        assigned_view_ids: set[int] = set()

        try:
            for index, product in enumerate(products, start=1):
                product_instance = get_product_match(
                    multi_tenant_company=multi_tenant_company,
                    product_id=product.get("product_id"),
                    sku=product.get("sku"),
                )
                result = run_upsert_product_updates(
                    import_process=tool_run,
                    multi_tenant_company=multi_tenant_company,
                    product=product_instance,
                    active=product.get("active"),
                    ean_code=product.get("ean_code"),
                    translations=product.get("translations"),
                    prices=product.get("prices"),
                    properties=product.get("properties"),
                    images=product.get("images"),
                    sales_channel_view_ids=product.get("sales_channel_view_ids"),
                )
                results.append(result)
                assigned_view_ids.update(product.get("sales_channel_view_ids", []))
                self.update_mcp_tool_run_progress(
                    tool_run=tool_run,
                    processed_records=index,
                    total_records=len(products),
                )
        except Exception as error:
            self.fail_mcp_tool_run(tool_run=tool_run, error=error)
            raise

        response = self.build_bulk_response(
            requested_count=len(products),
            processed_count=len(results),
            updated_count=len(results),
            results=results,
        )
        self.complete_mcp_tool_run(
            tool_run=tool_run,
            response_content=response,
            processed_records=len(results),
            assigned_view_ids=sorted(assigned_view_ids),
        )
        return response
