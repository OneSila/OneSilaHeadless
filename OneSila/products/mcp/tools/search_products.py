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
from media.models import Media, MediaProductThrough
from products.mcp.helpers import get_product_summary_queryset, serialize_product_summary
from products.mcp.output_types import SEARCH_PRODUCTS_OUTPUT_SCHEMA
from products.mcp.types import ProductTypeValue, SearchProductsPayload
from products.models import Product


class SearchProductsMcpTool(BaseMcpTool):
    name = "search_products"
    title = "Search Products"
    read_only = True
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
        select_value_id: Annotated[int | None, Field(ge=1, description="Filter products that use the given property select value database ID in single-select or multiselect properties.")] = None,
        has_images: Annotated[bool | None, Field(description="Filter by whether the product has any image assignments.")] = None,
        limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of results to return.")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of results to skip before returning matches.")] = 0,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Search company-scoped products by SKU, product type, VAT, inspector state, property assignments,
        select values, and image presence. Returns summary rows only. Use `get_product` for full detail
        once you know the exact SKU.

        Args:
            search: Search term to match against SKU and translated product names.
            sku: Optional partial SKU filter.
            type: Optional exact product type filter.
            active: Optional active/inactive filter.
            vat_rate: Optional exact VAT rate percentage filter.
            has_missing_information: Filter by any missing information flag from the product inspector.
            has_missing_required_information: Filter by missing required information from the product inspector.
            property_id: Optional property database ID filter.
            select_value_id: Optional property select value database ID filter.
            has_images: Optional image-presence filter.
            limit: Maximum number of results to return (default 20, max 100).
            offset: Number of results to skip for pagination.
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
                active=self._sanitize_optional_bool(value=active, field_name="active"),
                vat_rate=self._sanitize_optional_int(value=vat_rate, field_name="vat_rate", minimum=0),
                has_missing_information=self._sanitize_optional_bool(
                    value=has_missing_information,
                    field_name="has_missing_information",
                ),
                has_missing_required_information=self._sanitize_optional_bool(
                    value=has_missing_required_information,
                    field_name="has_missing_required_information",
                ),
                property_id=self._sanitize_optional_int(value=property_id, field_name="property_id", minimum=1),
                select_value_id=self._sanitize_optional_int(
                    value=select_value_id,
                    field_name="select_value_id",
                    minimum=1,
                ),
                has_images=self._sanitize_optional_bool(value=has_images, field_name="has_images"),
                limit=self._sanitize_limit(limit=limit),
                offset=self._sanitize_offset(offset=offset),
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

    def _sanitize_limit(self, *, limit: int) -> int:
        if not isinstance(limit, int) or limit < 1:
            raise McpToolError(f"limit must be a positive integer, got: {limit!r}")
        return min(limit, 100)

    def _sanitize_offset(self, *, offset: int) -> int:
        if not isinstance(offset, int) or offset < 0:
            raise McpToolError(f"offset must be a non-negative integer, got: {offset!r}")
        return offset

    def _sanitize_type(self, *, type: ProductTypeValue | None) -> ProductTypeValue | None:
        if type is None:
            return None
        allowed_types = {choice[0] for choice in Product.PRODUCT_TYPE_CHOICES}
        if type not in allowed_types:
            raise McpToolError(f"Invalid type: {type!r}. Allowed types are: {sorted(allowed_types)}")
        return type

    def _sanitize_optional_bool(self, *, value: bool | None, field_name: str) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise McpToolError(f"{field_name} must be a boolean value, got: {value!r}")
        return value

    def _sanitize_optional_int(self, *, value: int | None, field_name: str, minimum: int) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or value < minimum:
            raise McpToolError(f"{field_name} must be an integer >= {minimum}, got: {value!r}")
        return value

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
        select_value_id: int | None,
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
            queryset = queryset.filter(productproperty__property_id=property_id)

        if select_value_id is not None:
            queryset = queryset.filter(
                Q(productproperty__value_select_id=select_value_id)
                | Q(productproperty__value_multi_select__id=select_value_id)
            )

        if has_images is not None:
            image_assignments = MediaProductThrough.objects.filter(
                product_id=OuterRef("pk"),
                media__type=Media.IMAGE,
            )
            queryset = queryset.annotate(
                filter_has_images=Exists(image_assignments),
            ).filter(filter_has_images=has_images)

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
            "has_more": has_more,
            "offset": offset,
            "limit": limit,
            "results": [
                serialize_product_summary(product=product)
                for product in products
            ],
        }
