from enum import Enum

import strawberry
from django.db.models import Q
from strawberry import UNSET
from strawberry_django import filter_field as custom_filter

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from llm.models import BrandCustomPrompt, McpToolRun
from properties.schema.types.filters import PropertySelectValueFilter
from sales_channels.schema.types.filters import SalesChannelViewFilter


@filter(BrandCustomPrompt)
class BrandCustomPromptFilter(SearchFilterMixin):
    id: auto
    language: auto
    brand_value: PropertySelectValueFilter | None


@strawberry.enum
class McpToolRunToolEnum(Enum):
    GET_COMPANY_DETAILS = "get_company_details"
    SEARCH_PRODUCTS = "search_products"
    GET_PRODUCT = "get_product"
    SEARCH_SALES_CHANNELS = "search_sales_channels"
    CREATE_PRODUCTS = "create_products"
    UPSERT_PRODUCTS = "upsert_products"
    SEARCH_PROPERTIES = "search_properties"
    GET_PROPERTY = "get_property"
    SEARCH_PROPERTY_SELECT_VALUES = "search_property_select_values"
    GET_PROPERTY_SELECT_VALUE = "get_property_select_value"
    CREATE_PROPERTIES = "create_properties"
    EDIT_PROPERTIES = "edit_properties"
    CREATE_PROPERTY_SELECT_VALUES = "create_property_select_values"
    EDIT_PROPERTY_SELECT_VALUES = "edit_property_select_values"


@filter(McpToolRun)
class McpToolRunFilter(SearchFilterMixin):
    id: auto
    name: auto
    status: auto
    created_at: auto
    tool_name: auto
    assigned_views: SalesChannelViewFilter | None

    @custom_filter(name="tool")
    def tool(self, queryset, value: McpToolRunToolEnum | None, prefix: str):
        if value in (None, UNSET):
            return queryset, Q()

        return queryset, Q(tool_name=value.value)
