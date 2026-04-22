from __future__ import annotations

from typing import Annotated

from core.models.multi_tenant import MultiTenantCompany
from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import (
    TAG_GET,
    TAG_PROPERTIES,
    TAG_PROPERTY_SELECT_VALUES,
    tool_tags,
)
from properties.mcp.helpers import (
    get_property_select_value_detail_queryset,
    resolve_property_ids,
    serialize_property_select_value_detail,
)
from properties.mcp.output_types import GET_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
from properties.mcp.types import PropertySelectValueDetailPayload
from properties.models import PropertySelectValue


class GetPropertySelectValueMcpTool(BaseMcpTool):
    name = "get_property_select_value"
    title = "Get Property Select Value"
    read_only = True
    tags = tool_tags(TAG_GET, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
    output_schema = GET_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        select_value_id: Annotated[int | None, Field(ge=1, description="Exact property select-value database ID. Prefer this when you already know it.")] = None,
        value: Annotated[str | None, Field(description="Exact translated select-value text for natural-key lookup.")] = None,
        property_id: Annotated[int | None, Field(ge=1, description="Exact property database ID for natural-key lookup when select_value_id is unknown.")] = None,
        property_internal_name: Annotated[str | None, Field(description="Exact property internal name for natural-key lookup when select_value_id is unknown.")] = None,
        property_name: Annotated[str | None, Field(description="Exact translated property name for natural-key lookup when select_value_id is unknown.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get a single company-scoped property select value by exact identifier.
        Prefer `select_value_id` whenever you already know it. If you do not know the ID,
        you can do an exact natural-key lookup by combining `value` with a property identifier.
        If you only provide `value`, the lookup only succeeds when that value matches exactly one
        distinct select value in the authenticated company.

        When you are not sure which value is the correct one, call `search_property_select_values`
        first and then use the returned `select_value_id` here.

        Returned detail includes:
        - id, value, full_value_name
        - usage_count, thumbnail_url
        - parent property summary
        - translations: `[{language, value}]`
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            await ctx.info(
                f"Getting property select value for company_id={multi_tenant_company.id} "
                f"with select_value_id={select_value_id!r}, value={value!r}, "
                f"property_id={property_id!r}, property_internal_name={property_internal_name!r}, "
                f"property_name={property_name!r}."
            )

            response_data = await self._get_property_select_value(
                multi_tenant_company=multi_tenant_company,
                select_value_id=select_value_id,
                value=value,
                property_id=property_id,
                property_internal_name=property_internal_name,
                property_name=property_name,
            )

            await ctx.info(
                f"Loaded property select value id={response_data['id']} full_value_name={response_data['full_value_name']!r}."
            )
            return self.build_result(
                summary=f"Loaded property select value '{response_data['full_value_name']}'.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get property select value failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_property_select_value(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        select_value_id: int | None,
        value: str | None,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> PropertySelectValueDetailPayload:
        select_value = self._get_match(
            multi_tenant_company=multi_tenant_company,
            select_value_id=select_value_id,
            value=value,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )
        select_value = get_property_select_value_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=select_value.id)
        return serialize_property_select_value_detail(select_value=select_value)

    def _get_match(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        select_value_id: int | None,
        value: str | None,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> PropertySelectValue:
        queryset = PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
        )

        if select_value_id is not None:
            select_value = queryset.filter(id=select_value_id).first()
            if select_value is None:
                raise McpToolError(
                    f"Property select value with id {select_value_id} not found."
                )
            return select_value

        value = self.validate_required_string(
            value=value,
            field_name="value",
        )

        property_ids = self._resolve_property_ids(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )

        if property_ids is not None:
            if not property_ids:
                raise McpToolError("No property matched the provided property identifiers.")
            queryset = queryset.filter(property_id=property_ids[0])

        queryset = queryset.filter(propertyselectvaluetranslation__value__iexact=value)
        select_value_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[:2]
        )

        if not select_value_ids:
            raise McpToolError("Property select value not found.")

        if len(select_value_ids) > 1:
            if property_ids is None:
                raise McpToolError(
                    "Multiple property select values matched the provided value. "
                    "Provide property_id, property_internal_name, or property_name, "
                    "or use search_property_select_values first."
                )
            raise McpToolError(
                "Multiple property select values matched the provided property and value. "
                "Use search_property_select_values first and then call get_property_select_value with select_value_id."
            )

        return PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
        ).get(id=select_value_ids[0])

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
