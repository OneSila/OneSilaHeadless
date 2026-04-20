from __future__ import annotations

from typing import Annotated, Any

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CREATE, TAG_PRODUCTS, tool_tags
from llm.models import McpToolRun
from products.mcp.create_helpers import (
    build_create_product_data,
    run_create_product_with_sections,
)
from products.mcp.output_types import CREATE_PRODUCTS_OUTPUT_SCHEMA
from products.mcp.types import (
    CreateProductInputPayload,
    CreateProductsPayload,
    ProductImageInputPayload,
    ProductPriceUpsertInputPayload,
    ProductPropertyValueUpdateInputPayload,
    ProductTranslationUpsertInputPayload,
    ProductTypeValue,
)
from products.mcp.update_helpers import (
    sanitize_product_images_input,
    sanitize_product_prices_input,
    sanitize_product_property_updates_input,
    sanitize_product_translation_updates_input,
    sanitize_sales_channel_view_ids_input,
)


class CreateProductsMcpTool(BaseMcpTool):
    name = "create_products"
    title = "Create Products"
    tags = tool_tags(TAG_CREATE, TAG_PRODUCTS)
    output_schema = CREATE_PRODUCTS_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 10

    async def execute(
        self,
        products: Annotated[
            list[CreateProductInputPayload] | CreateProductInputPayload | str,
            Field(
                description=(
                    "Create 1 to 10 products. Each item requires `type` and `name`. Optional root fields: "
                    "`sku`, `product_type_id`, `product_type_value`, `vat_rate_id`, `vat_rate`, `active`, `ean_code`. "
                    "Optional nested sections: `translations`, `prices`, `properties`, `images`, `sales_channel_view_ids`. "
                    "Use `product_type_id` from `get_company_details(show_product_types=true)` or `product_type_value` when you know the exact product-type label. "
                    "Use `vat_rate_id` from `get_company_details(show_vat_rates=true)` or `vat_rate` with the exact configured percentage. "
                    "Use `image_content` for base64 uploaded images."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create one or more products for the authenticated company.

        Use this when the user wants brand-new products. A single object becomes a one-item batch,
        and the response always returns an array in `results`.

        Required per product:
        - `type`: SIMPLE, BUNDLE, CONFIGURABLE, or ALIAS
        - `name`

        Optional root fields:
        - `sku`: provide one, otherwise one is generated
        - `product_type_id` or `product_type_value`
        - `vat_rate_id` or `vat_rate`
        - `active`
        - `ean_code`

        Optional nested sections:
        - `translations`
        - `prices`
        - `properties`
        - `images`
        - `sales_channel_view_ids`

        Examples:
        - Minimal create: `{type: "SIMPLE", name: "Red Mug"}`
        - Create with price: `{type: "SIMPLE", name: "Red Mug", prices: [{currency: "GBP", price: "9.99"}]}`
        - Create with property select value: `{type: "SIMPLE", name: "Red Mug", properties: [{property_id: 12, value: 44, value_is_id: true}]}`
        - Create with property by internal name: `{type: "SIMPLE", name: "Red Mug", properties: [{property_internal_name: "material", value: "Ceramic"}]}`
        - Create with uploaded image: `{type: "SIMPLE", name: "Red Mug", images: [{image_content: "<base64>", is_main_image: true}]}`
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
                f"Creating {len(sanitized_products)} product(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"products": sanitized_products},
                total_records=len(sanitized_products),
            )
            response_data = await self._create_products(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                products=sanitized_products,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} product create request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create products failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_product_type(self, *, value) -> ProductTypeValue:
        if not isinstance(value, str):
            raise McpToolError(f"type must be a string, got: {value!r}")
        allowed_types = {"SIMPLE", "BUNDLE", "CONFIGURABLE", "ALIAS"}
        normalized_value = value.strip().upper()
        if normalized_value not in allowed_types:
            raise McpToolError(f"Invalid type: {value!r}. Allowed types are: {sorted(allowed_types)}")
        return normalized_value  # type: ignore[return-value]

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

    def _sanitize_product_item(
        self,
        *,
        product: dict[str, Any],
        multi_tenant_company,
    ) -> CreateProductInputPayload:
        product_type = self._sanitize_product_type(value=product.get("type"))
        name = self.validate_required_string(
            value=product.get("name"),
            field_name="name",
        )
        sanitized_product: CreateProductInputPayload = {
            "type": product_type,
            "name": name,
        }

        sanitized_sku = self._sanitize_optional_string(value=product.get("sku"))
        sanitized_product_type_value = self._sanitize_optional_string(value=product.get("product_type_value"))
        sanitized_ean_code = self._sanitize_optional_string(value=product.get("ean_code"))
        sanitized_active = self.sanitize_optional_bool(value=product.get("active"), field_name="active")
        sanitized_product_type_id = self.sanitize_optional_int(
            value=product.get("product_type_id"),
            field_name="product_type_id",
            minimum=1,
        )
        sanitized_vat_rate_id = self.sanitize_optional_int(
            value=product.get("vat_rate_id"),
            field_name="vat_rate_id",
            minimum=1,
        )
        sanitized_vat_rate = self.sanitize_optional_int(
            value=product.get("vat_rate"),
            field_name="vat_rate",
            minimum=0,
        )
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

        if sanitized_sku:
            sanitized_product["sku"] = sanitized_sku
        if sanitized_product_type_id is not None:
            sanitized_product["product_type_id"] = sanitized_product_type_id
        if sanitized_product_type_value:
            sanitized_product["product_type_value"] = sanitized_product_type_value
        if sanitized_vat_rate_id is not None:
            sanitized_product["vat_rate_id"] = sanitized_vat_rate_id
        if sanitized_vat_rate is not None:
            sanitized_product["vat_rate"] = sanitized_vat_rate
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
    def _create_products(
        self,
        *,
        multi_tenant_company,
        tool_run_id: int,
        products: list[CreateProductInputPayload],
    ) -> CreateProductsPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []
        created_count = 0
        assigned_view_ids: set[int] = set()

        try:
            for index, product in enumerate(products, start=1):
                product_data, sku_was_generated = build_create_product_data(
                    multi_tenant_company=multi_tenant_company,
                    name=product["name"],
                    product_type_code=product["type"],
                    sku=product.get("sku"),
                    product_type_id=product.get("product_type_id"),
                    product_type_value=product.get("product_type_value"),
                    vat_rate_id=product.get("vat_rate_id"),
                    vat_rate=product.get("vat_rate"),
                )
                result = run_create_product_with_sections(
                    import_process=tool_run,
                    multi_tenant_company=multi_tenant_company,
                    product_data=product_data,
                    sku=product.get("sku"),
                    sku_was_generated=sku_was_generated,
                    active=product.get("active"),
                    ean_code=product.get("ean_code"),
                    translations=product.get("translations"),
                    prices=product.get("prices"),
                    properties=product.get("properties"),
                    images=product.get("images"),
                    sales_channel_view_ids=product.get("sales_channel_view_ids"),
                )
                results.append(result)
                if result["created"]:
                    created_count += 1
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
            created_count=created_count,
            results=results,
        )
        self.complete_mcp_tool_run(
            tool_run=tool_run,
            response_content=response,
            processed_records=len(results),
            assigned_view_ids=sorted(assigned_view_ids),
        )
        return response
