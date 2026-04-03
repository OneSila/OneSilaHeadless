from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from django.db.models import Count, F, Q
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from properties.mcp.output_types import SEARCH_PROPERTIES_OUTPUT_SCHEMA
from properties.mcp.types import PropertySummaryPayload, PropertyTypeValue, SearchPropertiesPayload
from properties.models import Property


class SearchPropertiesMcpTool(BaseMcpTool):
    name = "search_properties"
    title = "Search Properties"
    read_only = True
    output_schema = SEARCH_PROPERTIES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        search: Annotated[str | None, Field(description="Optional free-text search across translated property names and internal names.")] = None,
        internal_name: Annotated[str | None, Field(description="Optional partial internal name filter.")] = None,
        is_public: Annotated[bool | None, Field(description="Filter public-information properties only, private properties only, or omit for both.")] = None,
        missing_main_translation: Annotated[bool | None, Field(description="Filter by whether the company default-language translation is missing.")] = None,
        missing_translations: Annotated[bool | None, Field(description="Filter by whether one or more enabled company language translations are missing.")] = None,
        used_in_products: Annotated[bool | None, Field(description="Filter by whether the property is already used on products.")] = None,
        type: Annotated[PropertyTypeValue | None, Field(description="Optional exact property type filter.")] = None,
        limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of results to return.")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of results to skip before returning matches.")] = 0,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Search company-scoped properties using the same kinds of filters exposed in GraphQL.
        Use this tool to narrow down candidate properties by translated name, internal name,
        type, translation completeness, and whether the property is already used on products.
        Returns summary records only. Use `get_property` for full details on a specific property.

        Args:
            search: Search term to match against translated property names and internal names.
            internal_name: Optional partial internal name filter.
            is_public: Optional filter for public-information properties.
            missing_main_translation: Filter by whether the company default-language translation is missing.
            missing_translations: Filter by whether translations are missing for one or more company languages.
            used_in_products: Filter by whether the property is already used on products.
            type: Optional property type filter.
            limit: Maximum number of results to return (default 20, max 100).
            offset: Number of results to skip for pagination.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            await ctx.info(
                f"Searching properties for company_id={multi_tenant_company.id} "
                f"with search={search!r}, internal_name={internal_name!r}, type={type!r}."
            )
            limit = self._sanitize_limit(limit=limit)
            offset = self._sanitize_offset(offset=offset)
            property_type = self._sanitize_type(type=type)
            is_public = self._sanitize_optional_bool(value=is_public, field_name="is_public")
            missing_main_translation = self._sanitize_optional_bool(
                value=missing_main_translation,
                field_name="missing_main_translation",
            )
            missing_translations = self._sanitize_optional_bool(
                value=missing_translations,
                field_name="missing_translations",
            )
            used_in_products = self._sanitize_optional_bool(
                value=used_in_products,
                field_name="used_in_products",
            )
            response_data = await self._search_properties(
                multi_tenant_company=multi_tenant_company,
                search=search,
                internal_name=internal_name,
                is_public=is_public,
                missing_main_translation=missing_main_translation,
                missing_translations=missing_translations,
                used_in_products=used_in_products,
                property_type=property_type,
                limit=limit,
                offset=offset,
            )

            await ctx.info(
                f"Property search returned {len(response_data['results'])} results; has_more={response_data['has_more']}."
            )
            return self.build_result(
                summary=f"Found {len(response_data['results'])} matching properties.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Property search failed: {error}")
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

    def _sanitize_type(self, *, type: PropertyTypeValue | None) -> PropertyTypeValue | None:
        if type is None:
            return None
        allowed_types = {choice[0] for choice in Property.TYPES.ALL}
        if type not in allowed_types:
            raise McpToolError(f"Invalid type: {type!r}. Allowed types are: {sorted(allowed_types)}")
        return type

    def _sanitize_optional_bool(self, *, value: bool | None, field_name: str) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise McpToolError(f"{field_name} must be a boolean value, got: {value!r}")
        return value

    @database_sync_to_async
    def _search_properties(
        self,
        *,
        multi_tenant_company,
        search: str | None,
        internal_name: str | None,
        is_public: bool | None,
        missing_main_translation: bool | None,
        missing_translations: bool | None,
        used_in_products: bool | None,
        property_type: PropertyTypeValue | None,
        limit: int,
        offset: int,
    ) -> SearchPropertiesPayload:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if search:
            queryset = queryset.filter(
                Q(propertytranslation__name__icontains=search)
                | Q(internal_name__icontains=search)
            )

        if internal_name:
            queryset = queryset.filter(internal_name__icontains=internal_name)

        if is_public is not None:
            queryset = queryset.filter(is_public_information=is_public)

        if property_type:
            queryset = queryset.filter(type=property_type)

        if used_in_products is not None:
            queryset = queryset.used_in_products(
                multi_tenant_company_id=multi_tenant_company.id,
                used=used_in_products,
            )

        if missing_main_translation is not None:
            condition = Q(
                propertytranslation__language=F("multi_tenant_company__language")
            ) & ~Q(propertytranslation__name="")
            if missing_main_translation:
                queryset = queryset.exclude(condition)
            else:
                queryset = queryset.filter(condition)

        if missing_translations is not None:
            required_count = len(multi_tenant_company.languages or [])
            queryset = queryset.annotate(
                translations_count=Count("propertytranslation__language", distinct=True)
            )
            if missing_translations:
                queryset = queryset.filter(translations_count__lt=required_count)
            else:
                queryset = queryset.filter(translations_count=required_count)

        property_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[offset:offset + limit + 1]
        )
        has_more = len(property_ids) > limit
        properties = list(
            Property.objects.filter(id__in=property_ids[:limit]).prefetch_related("propertytranslation_set").order_by("id")
        )

        return {
            "has_more": has_more,
            "offset": offset,
            "limit": limit,
            "results": [self._serialize_property_summary(property_instance=property) for property in properties],
        }

    def _serialize_property_summary(self, *, property_instance: Property) -> PropertySummaryPayload:
        return {
            "id": property_instance.id,
            "name": property_instance.name,
            "internal_name": property_instance.internal_name,
            "type": property_instance.type,
            "type_label": property_instance.get_type_display(),
            "is_public_information": property_instance.is_public_information,
            "add_to_filters": property_instance.add_to_filters,
            "has_image": property_instance.has_image,
        }
