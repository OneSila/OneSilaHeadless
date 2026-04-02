from __future__ import annotations

from django.db.models import Count, F, Q

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.serializers import json_response
from properties.models import Property


class SearchPropertiesMcpTool(BaseMcpTool):
    name = "search_properties"
    read_only = True

    def execute(
        self,
        search: str | None = None,
        internal_name: str | None = None,
        is_public: bool | None = None,
        missing_main_translation: bool | None = None,
        missing_translations: bool | None = None,
        used_in_products: bool | None = None,
        type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """
        Search properties using the same kinds of filters exposed in GraphQL.
        Returns a summary list. Use get_property for full details on one property.

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
            multi_tenant_company = self.get_multi_tenant_company(required=True)
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

            return json_response(
                data={
                    "has_more": has_more,
                    "offset": offset,
                    "limit": limit,
                    "results": [self._serialize_property_summary(property_instance=property) for property in properties],
                }
            )
        except Exception as error:
            return self.handle_error(error=error, action=self.name)

    def _sanitize_limit(self, *, limit: int) -> int:
        if not isinstance(limit, int) or limit < 1:
            raise McpToolError(f"limit must be a positive integer, got: {limit!r}")
        return min(limit, 100)

    def _sanitize_offset(self, *, offset: int) -> int:
        if not isinstance(offset, int) or offset < 0:
            raise McpToolError(f"offset must be a non-negative integer, got: {offset!r}")
        return offset

    def _sanitize_type(self, *, type: str | None) -> str | None:
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

    def _serialize_property_summary(self, *, property_instance: Property) -> dict:
        return {
            "id": property_instance.id,
            "name": property_instance.name,
            "internal_name": property_instance.internal_name,
            "type": property_instance.type,
            "is_public_information": property_instance.is_public_information,
            "add_to_filters": property_instance.add_to_filters,
            "has_image": property_instance.has_image,
        }
