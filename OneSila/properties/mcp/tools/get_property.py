from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from properties.mcp.helpers import get_property_detail_queryset, serialize_property_detail
from properties.mcp.output_types import GET_PROPERTY_OUTPUT_SCHEMA
from properties.mcp.types import PropertyDetailPayload
from properties.models import Property


class GetPropertyMcpTool(BaseMcpTool):
    name = "get_property"
    title = "Get Property"
    read_only = True
    output_schema = GET_PROPERTY_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        property_id: Annotated[int | None, Field(ge=1, description="Exact property database ID.")] = None,
        internal_name: Annotated[str | None, Field(description="Exact property internal name.")] = None,
        name: Annotated[str | None, Field(description="Exact translated property name within the authenticated company.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Get a single company-scoped property by exact identifier.
        Use this when you already know the property ID, exact internal name, or exact translated name
        and you need the full property details, translations, and select values.

        Args:
            property_id: The database id of the property.
            internal_name: Exact property internal name.
            name: Exact translated property name.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            await ctx.info(
                f"Getting property for company_id={multi_tenant_company.id} "
                f"with property_id={property_id!r}, internal_name={internal_name!r}, name={name!r}."
            )
            response_data = await self._get_property_detail(
                multi_tenant_company=multi_tenant_company,
                property_id=property_id,
                internal_name=internal_name,
                name=name,
            )
            await ctx.info(
                f"Loaded property_id={response_data['id']} internal_name={response_data['internal_name']!r}."
            )
            return self.build_result(
                summary=f"Loaded property '{response_data['name']}' ({response_data['type_label']}).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Get property failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    @database_sync_to_async
    def _get_property_detail(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        internal_name: str | None,
        name: str | None,
    ) -> PropertyDetailPayload:
        property_instance = self._get_property_match(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            internal_name=internal_name,
            name=name,
        )
        property_instance = get_property_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=property_instance.id)
        return serialize_property_detail(property_instance=property_instance)

    def _get_property_match(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        internal_name: str | None,
        name: str | None,
    ) -> Property:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if property_id is not None and not isinstance(property_id, int):
            raise McpToolError(f"property_id must be an integer, got: {type(property_id).__name__}")

        if not any([property_id is not None, internal_name, name]):
            raise McpToolError("Provide property_id, internal_name, or name.")

        if property_id is not None:
            queryset = queryset.filter(id=property_id)
        if internal_name:
            queryset = queryset.filter(internal_name__iexact=internal_name)
        if name:
            queryset = queryset.filter(propertytranslation__name__iexact=name)

        property_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[:2]
        )

        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided identifiers.")

        return queryset.get(id=property_ids[0])
