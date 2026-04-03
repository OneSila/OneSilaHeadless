from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from imports_exports.factories.properties import ImportPropertySelectValueInstance
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from properties.mcp.helpers import (
    build_import_process,
    get_property_select_value_detail_queryset,
    sanitize_select_value_translations_input,
    serialize_property_select_value_detail,
    validate_select_value_translation_languages,
)
from properties.mcp.output_types import CREATE_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
from properties.mcp.types import (
    CreatePropertySelectValuePayload,
    PropertySelectValueTranslationInputPayload,
)
from properties.models import Property, PropertySelectValue


class CreatePropertySelectValueMcpTool(BaseMcpTool):
    name = "create_property_select_value"
    title = "Create Property Select Value"
    output_schema = CREATE_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        value: Annotated[
            str,
            Field(
                description=(
                    "Main select-value text in the company's default language. "
                    "This is required and will be used as the default translation."
                )
            ),
        ] = ...,
        property_id: Annotated[int | None, Field(ge=1, description="Exact property database ID to attach this value to.")] = None,
        property_internal_name: Annotated[str | None, Field(description="Exact property internal name to attach this value to.")] = None,
        property_name: Annotated[str | None, Field(description="Exact translated property name to attach this value to.")] = None,
        translations: Annotated[
            list[PropertySelectValueTranslationInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of translated select-value texts. Translation languages must belong to "
                    "the authenticated company's enabled languages. Use get_company_languages first to see "
                    "the allowed language codes. If the client sends JSON-stringified arguments, a JSON string "
                    "array is also accepted."
                )
            ),
        ] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create or reuse a property select value for an existing property.
        Provide the parent property by exact property_id, exact internal_name, or exact translated property name.
        The required `value` is treated as the default-language translation, and optional translations can be
        provided for other enabled company languages.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_value = self.validate_required_string(value=value, field_name="value")
            translations_payload = self._sanitize_translations(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )

            await ctx.info(
                f"Creating property select value for company_id={multi_tenant_company.id} "
                f"with value={sanitized_value!r}, property_id={property_id!r}, "
                f"property_internal_name={property_internal_name!r}, property_name={property_name!r}."
            )

            response_data = await self._create_property_select_value(
                multi_tenant_company=multi_tenant_company,
                value=sanitized_value,
                property_id=property_id,
                property_internal_name=property_internal_name,
                property_name=property_name,
                translations=translations_payload,
            )

            action = "Created" if response_data["created"] else "Updated existing"
            await ctx.info(
                f"{action} property select value id={response_data['select_value']['id']} "
                f"for property_id={response_data['select_value']['property']['id']}."
            )

            return self.build_result(
                summary=f"{action} property select value '{response_data['select_value']['full_value_name']}'.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create property select value failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_translations(
        self,
        *,
        translations: list[PropertySelectValueTranslationInputPayload] | str | None,
        multi_tenant_company: MultiTenantCompany,
    ) -> list[PropertySelectValueTranslationInputPayload] | None:
        try:
            sanitized_translations = sanitize_select_value_translations_input(translations=translations)
            validate_select_value_translation_languages(
                translations=sanitized_translations,
                multi_tenant_company=multi_tenant_company,
            )
            return sanitized_translations
        except ValueError as error:
            raise McpToolError(str(error)) from error

    @database_sync_to_async
    def _create_property_select_value(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        value: str,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
        translations: list[PropertySelectValueTranslationInputPayload] | None,
    ) -> CreatePropertySelectValuePayload:
        property_instance = self._resolve_property(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )

        select_value_data = {"value": value}
        if translations is not None:
            select_value_data["translations"] = translations

        try:
            import_instance = ImportPropertySelectValueInstance(
                select_value_data,
                import_process=build_import_process(multi_tenant_company=multi_tenant_company),
                property=property_instance,
            )
            import_instance.process()
        except ValueError as error:
            raise McpToolError(str(error)) from error

        select_value_instance = get_property_select_value_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=import_instance.instance.id)

        return {
            "created": bool(getattr(import_instance, "created", False)),
            "select_value": serialize_property_select_value_detail(select_value=select_value_instance),
        }

    def _resolve_property(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> Property:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if not any([property_id is not None, property_internal_name, property_name]):
            raise McpToolError("Provide property_id, property_internal_name, or property_name.")

        if property_id is not None:
            queryset = queryset.filter(id=property_id)
        if property_internal_name:
            queryset = queryset.filter(internal_name__iexact=property_internal_name)
        if property_name:
            queryset = queryset.filter(propertytranslation__name__iexact=property_name)

        property_ids = list(queryset.order_by("id").values_list("id", flat=True).distinct()[:2])
        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided property identifiers.")

        return Property.objects.get(id=property_ids[0])
