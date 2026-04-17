from __future__ import annotations

from typing import Annotated

from core.models.multi_tenant import MultiTenantCompany
from channels.db import database_sync_to_async
from django.db.models import Count, F, Q
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import (
    TAG_PROPERTIES,
    TAG_PROPERTY_SELECT_VALUES,
    TAG_SEARCH,
    tool_tags,
)
from properties.mcp.helpers import (
    get_property_select_value_detail_queryset,
    resolve_property_ids,
    serialize_property_select_value_search_result,
)
from properties.mcp.output_types import SEARCH_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
from properties.mcp.types import (
    PropertySelectValueSearchResultPayload,
    SearchPropertySelectValuesPayload,
)
from properties.models import PropertySelectValue


class SearchPropertySelectValuesMcpTool(BaseMcpTool):
    name = "search_property_select_values"
    title = "Search Property Select Values"
    read_only = True
    tags = tool_tags(TAG_SEARCH, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
    output_schema = SEARCH_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        search: Annotated[str | None, Field(description="Free-text search across values, property names, and internal names.")] = None,
        property_id: Annotated[int | None, Field(ge=1, description="Exact property database ID to scope the search.")] = None,
        property_internal_name: Annotated[str | None, Field(description="Exact property internal name to scope the search.")] = None,
        property_name: Annotated[str | None, Field(description="Exact translated property name to scope the search within the authenticated company.")] = None,
        missing_main_translation: Annotated[bool | None, Field(description="Filter by whether the company default-language translation is missing.")] = None,
        missing_translations: Annotated[bool | None, Field(description="Filter by whether one or more enabled company language translations are missing.")] = None,
        used_in_products: Annotated[bool | None, Field(description="Filter by whether the select value is already used on products.")] = None,
        is_product_type: Annotated[bool | None, Field(description="Filter by whether the parent property is the product-type property.")] = None,
        include_translations: Annotated[bool, Field(description="Include translations in each search result as translations:[{language,value}].")] = False,
        include_usage_count: Annotated[bool, Field(description="Include usage counts in each search result.")] = False,
        limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of results to return.")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of results to skip before returning matches.")] = 0,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Search company-scoped property select values.
        Use this tool when you know the translated value text only approximately, need to filter by
        translation completeness or product usage, or need to find the correct select-value ID before
        calling `get_property_select_value`.

        When you need a deterministic detail lookup, search first and then call `get_property_select_value`
        with the returned select-value ID.

        Each result contains:
        - id, value
        - property: {id, name, internal_name, type, type_label, is_product_type}
        - optional translations when `include_translations=true`
        - optional usage_count when `include_usage_count=true`
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            await ctx.info(
                f"Searching property select values for company_id={multi_tenant_company.id} "
                f"with search={search!r}, property_id={property_id!r}, "
                f"property_internal_name={property_internal_name!r}, property_name={property_name!r}."
            )

            limit = self.sanitize_limit(limit=limit)
            offset = self.sanitize_offset(offset=offset)
            missing_main_translation = self.sanitize_optional_bool(
                value=missing_main_translation,
                field_name="missing_main_translation",
            )
            missing_translations = self.sanitize_optional_bool(
                value=missing_translations,
                field_name="missing_translations",
            )
            used_in_products = self.sanitize_optional_bool(
                value=used_in_products,
                field_name="used_in_products",
            )
            is_product_type = self.sanitize_optional_bool(
                value=is_product_type,
                field_name="is_product_type",
            )
            response_data = await self._search_property_select_values(
                multi_tenant_company=multi_tenant_company,
                search=search,
                property_id=property_id,
                property_internal_name=property_internal_name,
                property_name=property_name,
                missing_main_translation=missing_main_translation,
                missing_translations=missing_translations,
                used_in_products=used_in_products,
                is_product_type=is_product_type,
                include_translations=include_translations,
                include_usage_count=include_usage_count,
                limit=limit,
                offset=offset,
            )

            await ctx.info(
                f"Property select value search returned {len(response_data['results'])} results; "
                f"has_more={response_data['has_more']}."
            )
            return self.build_result(
                summary=f"Found {len(response_data['results'])} matching property select values.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Property select value search failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _apply_property_scope(
        self,
        *,
        queryset,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ):
        property_ids = self._resolve_property_ids(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )
        if property_ids is None:
            return queryset
        if not property_ids:
            return queryset.none()
        return queryset.filter(property_id=property_ids[0])

    def _resolve_property_ids(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> list[int] | None:
        property_ids = resolve_property_ids(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )
        if property_ids is not None and len(property_ids) > 1:
            raise McpToolError(
                "Multiple properties matched the provided property identifiers."
            )
        return property_ids

    @database_sync_to_async
    def _search_property_select_values(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        search: str | None,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
        missing_main_translation: bool | None,
        missing_translations: bool | None,
        used_in_products: bool | None,
        is_product_type: bool | None,
        include_translations: bool,
        include_usage_count: bool,
        limit: int,
        offset: int,
    ) -> SearchPropertySelectValuesPayload:
        queryset = PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
        )
        queryset = self._apply_property_scope(
            queryset=queryset,
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )

        if search:
            queryset = queryset.filter(
                Q(propertyselectvaluetranslation__value__icontains=search)
                | Q(property__propertytranslation__name__icontains=search)
                | Q(property__internal_name__icontains=search)
            )

        if is_product_type is not None:
            queryset = queryset.filter(property__is_product_type=is_product_type)

        if used_in_products is not None:
            queryset = queryset.used_in_products(
                multi_tenant_company_id=multi_tenant_company.id,
                used=used_in_products,
            )

        if missing_main_translation is not None:
            condition = Q(
                propertyselectvaluetranslation__language=F("multi_tenant_company__language")
            ) & ~Q(propertyselectvaluetranslation__value="")
            if missing_main_translation:
                queryset = queryset.exclude(condition)
            else:
                queryset = queryset.filter(condition)

        if missing_translations is not None:
            required_count = len(multi_tenant_company.languages or [])
            queryset = queryset.annotate(
                translations_count=Count(
                    "propertyselectvaluetranslation__language",
                    distinct=True,
                )
            )
            if missing_translations:
                queryset = queryset.filter(translations_count__lt=required_count)
            else:
                queryset = queryset.filter(translations_count=required_count)

        total_count = queryset.values("id").distinct().count()
        select_value_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[offset:offset + limit + 1]
        )
        has_more = len(select_value_ids) > limit

        values = list(
            get_property_select_value_detail_queryset(
                multi_tenant_company=multi_tenant_company,
            ).filter(id__in=select_value_ids[:limit]).order_by("id")
        )

        return {
            "total_count": total_count,
            "has_more": has_more,
            "offset": offset,
            "limit": limit,
            "results": [
                self._serialize_select_value_summary(
                    select_value=value,
                    include_translations=include_translations,
                    include_usage_count=include_usage_count,
                )
                for value in values
            ],
        }

    def _serialize_select_value_summary(
        self,
        *,
        select_value: PropertySelectValue,
        include_translations: bool,
        include_usage_count: bool,
    ) -> PropertySelectValueSearchResultPayload:
        return serialize_property_select_value_search_result(
            select_value=select_value,
            include_translations=include_translations,
            include_usage_count=include_usage_count,
        )
