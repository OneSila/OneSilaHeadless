from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from django.db.models import Exists, OuterRef, Q
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_PRODUCTS, TAG_SEARCH, tool_tags
from media.models import Media, MediaProductThrough
from products.mcp.helpers import get_product_summary_queryset, serialize_product_search_summary
from products.mcp.output_types import SEARCH_PRODUCTS_OUTPUT_SCHEMA
from products.mcp.types import ProductTypeValue, SearchProductsPayload
from products.models import Product
from products_inspector.constants import ERROR_TYPES
from products_inspector.models import InspectorBlock
from properties.models import ProductProperty
from sales_channels.models import SalesChannelViewAssign


class SearchProductsMcpTool(BaseMcpTool):
    name = "search_products"
    title = "Search Products"
    read_only = True
    tags = tool_tags(TAG_SEARCH, TAG_PRODUCTS)
    output_schema = SEARCH_PRODUCTS_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        search: Annotated[str | None, Field(description="Optional free-text search across SKU and translated product names.")] = None,
        sku: Annotated[str | None, Field(description="Optional partial SKU filter.")] = None,
        type: Annotated[ProductTypeValue | None, Field(description="Optional exact product type filter.")] = None,
        active: Annotated[bool | None, Field(description="Filter active products only, inactive products only, or omit for both.")] = None,
        vat_rate: Annotated[int | None, Field(ge=0, description="Optional exact VAT rate percentage filter, for example 21.")] = None,
        has_missing_information: Annotated[bool | None, Field(description="Filter by whether the product inspector reports any missing information, required or optional.")] = None,
        has_missing_required_information: Annotated[bool | None, Field(description="Filter by whether the product inspector reports missing required information.")] = None,
        property_id: Annotated[int | None, Field(ge=1, description="Filter products that have a value assigned for the given property database ID.")] = None,
        exclude_property_id: Annotated[int | None, Field(ge=1, description="Filter products that do not have a value assigned for the given property database ID.")] = None,
        select_value_id: Annotated[int | None, Field(ge=1, description="Filter products that use the given property select value database ID in single-select or multiselect properties.")] = None,
        exclude_select_value_id: Annotated[int | None, Field(ge=1, description="Filter products that do not use the given property select value database ID in single-select or multiselect properties.")] = None,
        assigned_to_sales_channel_view_id: Annotated[int | None, Field(ge=1, description="Filter products assigned to the given sales channel view ID.")] = None,
        not_assigned_to_sales_channel_view_id: Annotated[int | None, Field(ge=1, description="Filter products not assigned to the given sales channel view ID.")] = None,
        inspector_not_successfully_code_error: Annotated[int | None, Field(ge=1, description="Filter products with the given unresolved inspector block error code. Use `onesila://products/inspector-error-codes` for supported codes such as missing images or missing prices.")] = None,
        has_images: Annotated[bool | None, Field(description="Filter by whether the product has any image assignments.")] = None,
        limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of results to return.")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of results to skip before returning matches.")] = 0,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Search company-scoped products by SKU, product type, VAT, inspector state, property assignments,
        select values, and image presence. Returns summary rows only. Use `get_product` for full detail
        once you know the exact SKU.

        Each summary result contains:
        - id, sku, name
        - type and type_label
        - active
        - vat_rate
        - thumbnail_url
        - has_images
        - missing-information flags

        Common workflows:
        - missing images: `has_images=false`
        - missing a property assignment: `exclude_property_id=<id>`
        - missing a select value: `exclude_select_value_id=<id>`
        - assigned to a storefront view: `assigned_to_sales_channel_view_id=<view_id>`
        - unresolved inspector issue such as missing images: `inspector_not_successfully_code_error=<code>`
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            await ctx.info(
                f"Searching products for company_id={multi_tenant_company.id} "
                f"with search={search!r}, sku={sku!r}, type={type!r}."
            )
            response_data = await self._search_products(
                multi_tenant_company=multi_tenant_company,
                search=search,
                sku=sku,
                product_type=self._sanitize_type(type=type),
                active=self.sanitize_optional_bool(value=active, field_name="active"),
                vat_rate=self.sanitize_optional_int(value=vat_rate, field_name="vat_rate", minimum=0),
                has_missing_information=self.sanitize_optional_bool(
                    value=has_missing_information,
                    field_name="has_missing_information",
                ),
                has_missing_required_information=self.sanitize_optional_bool(
                    value=has_missing_required_information,
                    field_name="has_missing_required_information",
                ),
                property_id=self.sanitize_optional_int(value=property_id, field_name="property_id", minimum=1),
                exclude_property_id=self.sanitize_optional_int(
                    value=exclude_property_id,
                    field_name="exclude_property_id",
                    minimum=1,
                ),
                select_value_id=self.sanitize_optional_int(
                    value=select_value_id,
                    field_name="select_value_id",
                    minimum=1,
                ),
                exclude_select_value_id=self.sanitize_optional_int(
                    value=exclude_select_value_id,
                    field_name="exclude_select_value_id",
                    minimum=1,
                ),
                assigned_to_sales_channel_view_id=self.sanitize_optional_int(
                    value=assigned_to_sales_channel_view_id,
                    field_name="assigned_to_sales_channel_view_id",
                    minimum=1,
                ),
                not_assigned_to_sales_channel_view_id=self.sanitize_optional_int(
                    value=not_assigned_to_sales_channel_view_id,
                    field_name="not_assigned_to_sales_channel_view_id",
                    minimum=1,
                ),
                inspector_not_successfully_code_error=self._sanitize_inspector_error_code(
                    error_code=inspector_not_successfully_code_error,
                ),
                has_images=self.sanitize_optional_bool(value=has_images, field_name="has_images"),
                limit=self.sanitize_limit(limit=limit),
                offset=self.sanitize_offset(offset=offset),
            )
            await ctx.info(
                f"Product search returned {len(response_data['results'])} results; has_more={response_data['has_more']}."
            )
            return self.build_result(
                summary=f"Found {len(response_data['results'])} matching products.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Product search failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_type(self, *, type: ProductTypeValue | None) -> ProductTypeValue | None:
        if type is None:
            return None
        allowed_types = {choice[0] for choice in Product.PRODUCT_TYPE_CHOICES}
        if type not in allowed_types:
            raise McpToolError(f"Invalid type: {type!r}. Allowed types are: {sorted(allowed_types)}")
        return type

    def _sanitize_inspector_error_code(self, *, error_code: int | None) -> int | None:
        if error_code is None:
            return None

        error_code = self.sanitize_optional_int(
            value=error_code,
            field_name="inspector_not_successfully_code_error",
            minimum=1,
        )
        allowed_error_codes = {code for code, _label in ERROR_TYPES}
        if error_code not in allowed_error_codes:
            raise McpToolError(
                "Invalid inspector_not_successfully_code_error: "
                f"{error_code!r}. Use onesila://products/inspector-error-codes for supported codes."
            )
        return error_code

    @database_sync_to_async
    def _search_products(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        search: str | None,
        sku: str | None,
        product_type: ProductTypeValue | None,
        active: bool | None,
        vat_rate: int | None,
        has_missing_information: bool | None,
        has_missing_required_information: bool | None,
        property_id: int | None,
        exclude_property_id: int | None,
        select_value_id: int | None,
        exclude_select_value_id: int | None,
        assigned_to_sales_channel_view_id: int | None,
        not_assigned_to_sales_channel_view_id: int | None,
        inspector_not_successfully_code_error: int | None,
        has_images: bool | None,
        limit: int,
        offset: int,
    ) -> SearchProductsPayload:
        queryset = Product.objects.filter(
            multi_tenant_company=multi_tenant_company,
        )

        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search)
                | Q(translations__name__icontains=search)
            )

        if sku:
            queryset = queryset.filter(sku__icontains=sku)

        if product_type:
            queryset = queryset.filter(type=product_type)

        if active is not None:
            queryset = queryset.filter(active=active)

        if vat_rate is not None:
            queryset = queryset.filter(vat_rate__rate=vat_rate)

        if has_missing_required_information is True:
            queryset = queryset.filter(inspector__has_missing_information=True)
        elif has_missing_required_information is False:
            queryset = queryset.filter(
                Q(inspector__has_missing_information=False) | Q(inspector__isnull=True)
            )

        if has_missing_information is True:
            queryset = queryset.filter(
                Q(inspector__has_missing_information=True)
                | Q(inspector__has_missing_optional_information=True)
            )
        elif has_missing_information is False:
            queryset = queryset.filter(
                (
                    Q(inspector__has_missing_information=False)
                    & Q(inspector__has_missing_optional_information=False)
                )
                | Q(inspector__isnull=True)
            )

        if property_id is not None:
            property_assignments = ProductProperty.objects.filter(
                product_id=OuterRef("pk"),
                property_id=property_id,
            )
            queryset = queryset.annotate(
                has_property_assignment=Exists(property_assignments),
            ).filter(has_property_assignment=True)

        if exclude_property_id is not None:
            excluded_property_assignments = ProductProperty.objects.filter(
                product_id=OuterRef("pk"),
                property_id=exclude_property_id,
            )
            queryset = queryset.annotate(
                has_excluded_property_assignment=Exists(excluded_property_assignments),
            ).filter(has_excluded_property_assignment=False)

        if select_value_id is not None:
            select_value_assignments = ProductProperty.objects.filter(
                product_id=OuterRef("pk"),
            ).filter(
                Q(value_select_id=select_value_id)
                | Q(value_multi_select__id=select_value_id)
            )
            queryset = queryset.annotate(
                has_select_value_assignment=Exists(select_value_assignments),
            ).filter(has_select_value_assignment=True)

        if exclude_select_value_id is not None:
            excluded_select_value_assignments = ProductProperty.objects.filter(
                product_id=OuterRef("pk"),
            ).filter(
                Q(value_select_id=exclude_select_value_id)
                | Q(value_multi_select__id=exclude_select_value_id)
            )
            queryset = queryset.annotate(
                has_excluded_select_value_assignment=Exists(excluded_select_value_assignments),
            ).filter(has_excluded_select_value_assignment=False)

        if assigned_to_sales_channel_view_id is not None:
            view_assignments = SalesChannelViewAssign.objects.filter(
                product_id=OuterRef("pk"),
                sales_channel_view_id=assigned_to_sales_channel_view_id,
            )
            queryset = queryset.annotate(
                assigned_to_view=Exists(view_assignments),
            ).filter(assigned_to_view=True)

        if not_assigned_to_sales_channel_view_id is not None:
            excluded_view_assignments = SalesChannelViewAssign.objects.filter(
                product_id=OuterRef("pk"),
                sales_channel_view_id=not_assigned_to_sales_channel_view_id,
            )
            queryset = queryset.annotate(
                assigned_to_excluded_view=Exists(excluded_view_assignments),
            ).filter(assigned_to_excluded_view=False)

        if inspector_not_successfully_code_error is not None:
            error_blocks = InspectorBlock.objects.filter(
                inspector__product_id=OuterRef("pk"),
                successfully_checked=False,
                error_code=inspector_not_successfully_code_error,
            )
            queryset = queryset.annotate(
                has_matching_inspector_error=Exists(error_blocks),
            ).filter(has_matching_inspector_error=True)

        if has_images is not None:
            image_assignments = MediaProductThrough.objects.filter(
                product_id=OuterRef("pk"),
                media__type=Media.IMAGE,
            )
            queryset = queryset.annotate(
                filter_has_images=Exists(image_assignments),
            ).filter(filter_has_images=has_images)

        total_count = queryset.values("id").distinct().count()
        product_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[offset:offset + limit + 1]
        )
        has_more = len(product_ids) > limit
        products = list(
            get_product_summary_queryset(
                multi_tenant_company=multi_tenant_company,
            ).filter(id__in=product_ids[:limit]).order_by("id")
        )

        return {
            "total_count": total_count,
            "has_more": has_more,
            "offset": offset,
            "limit": limit,
            "results": [
                serialize_product_search_summary(product=product)
                for product in products
            ],
        }
