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
from llm.mcp.tags import (
    TAG_CREATE,
    TAG_PROPERTIES,
    TAG_PROPERTY_SELECT_VALUES,
    tool_tags,
)
from properties.mcp.helpers import (
    build_select_value_mutation_payload,
    build_import_process,
    resolve_property_ids,
    sanitize_select_value_translations_input,
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
    tags = tool_tags(TAG_CREATE, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
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
                description="Translations as [{language, value}] pairs. Call get_company_languages for valid codes."
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
                f"{action} property select value id={response_data['select_value_id']} "
                f"for property_id={response_data['property_id']}."
            )

            return self.build_result(
                summary=f"{action} property select value '{response_data['full_value_name']}'.",
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

        return build_select_value_mutation_payload(
            select_value=import_instance.instance,
            created=bool(getattr(import_instance, "created", False)),
        )

    def _resolve_property(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> Property:
        if not any([property_id is not None, property_internal_name, property_name]):
            raise McpToolError("Provide property_id, property_internal_name, or property_name.")
        property_ids = resolve_property_ids(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            property_internal_name=property_internal_name,
            property_name=property_name,
        )
        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided property identifiers.")

        return Property.objects.get(id=property_ids[0])
