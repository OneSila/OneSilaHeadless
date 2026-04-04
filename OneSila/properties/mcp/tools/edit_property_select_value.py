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
    TAG_EDIT,
    TAG_PROPERTIES,
    TAG_PROPERTY_SELECT_VALUES,
    tool_tags,
)
from properties.mcp.helpers import (
    build_import_process,
    get_property_select_value_detail_queryset,
    sanitize_select_value_translations_input,
    serialize_property_select_value_detail,
    validate_select_value_translation_languages,
)
from properties.mcp.output_types import EDIT_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
from properties.mcp.types import (
    EditPropertySelectValuePayload,
    PropertySelectValueTranslationInputPayload,
)
from properties.models import PropertySelectValue


class EditPropertySelectValueMcpTool(BaseMcpTool):
    name = "edit_property_select_value"
    title = "Edit Property Select Value"
    tags = tool_tags(TAG_EDIT, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
    output_schema = EDIT_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        select_value_id: Annotated[int, Field(ge=1, description="Exact property select-value database ID to update.")] = ...,
        translations: Annotated[
            list[PropertySelectValueTranslationInputPayload] | str,
            Field(
                description=(
                    "Translated select-value texts to update or add. Translation languages must belong to "
                    "the authenticated company's enabled languages. Use get_company_languages first to see "
                    "the allowed language codes. If the client sends JSON-stringified arguments, a JSON string "
                    "array is also accepted."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Edit an existing company-scoped property select value by exact select_value_id.
        This tool only updates translations. It reuses the existing default-language value internally
        because the underlying import flow requires a base `value`, but the editable surface here is
        intentionally limited to translation updates and additions.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            translations_payload = self._sanitize_translations(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )

            await ctx.info(
                f"Editing property select value for company_id={multi_tenant_company.id} "
                f"with select_value_id={select_value_id!r}."
            )

            response_data = await self._edit_property_select_value(
                multi_tenant_company=multi_tenant_company,
                select_value_id=select_value_id,
                translations=translations_payload,
            )

            await ctx.info(
                f"Updated property select value id={response_data['select_value']['id']} "
                f"for property_id={response_data['select_value']['property']['id']}."
            )

            return self.build_result(
                summary=f"Updated property select value '{response_data['select_value']['full_value_name']}'.",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Edit property select value failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_translations(
        self,
        *,
        translations: list[PropertySelectValueTranslationInputPayload] | str,
        multi_tenant_company: MultiTenantCompany,
    ) -> list[PropertySelectValueTranslationInputPayload]:
        try:
            sanitized_translations = sanitize_select_value_translations_input(translations=translations)
            validate_select_value_translation_languages(
                translations=sanitized_translations,
                multi_tenant_company=multi_tenant_company,
            )
        except ValueError as error:
            raise McpToolError(str(error)) from error

        if not sanitized_translations:
            raise McpToolError("Provide at least one translation to update.")

        return sanitized_translations

    @database_sync_to_async
    def _edit_property_select_value(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        select_value_id: int,
        translations: list[PropertySelectValueTranslationInputPayload],
    ) -> EditPropertySelectValuePayload:
        select_value_instance = self._get_select_value(
            multi_tenant_company=multi_tenant_company,
            select_value_id=select_value_id,
        )

        select_value_data = {
            "value": select_value_instance.value,
            "translations": translations,
        }

        try:
            import_instance = ImportPropertySelectValueInstance(
                select_value_data,
                import_process=build_import_process(multi_tenant_company=multi_tenant_company),
                property=select_value_instance.property,
                instance=select_value_instance,
            )
            import_instance.process()
        except ValueError as error:
            raise McpToolError(str(error)) from error

        select_value_instance = get_property_select_value_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=select_value_instance.id)

        return {
            "updated": True,
            "select_value": serialize_property_select_value_detail(select_value=select_value_instance),
        }

    def _get_select_value(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        select_value_id: int,
    ) -> PropertySelectValue:
        select_value = PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            id=select_value_id,
        ).first()
        if select_value is None:
            raise McpToolError(f"Property select value with id {select_value_id} not found.")
        return select_value
