from __future__ import annotations

from typing import Annotated, Any

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
from llm.models import McpToolRun
from properties.mcp.helpers import (
    build_select_value_mutation_payload,
    sanitize_select_value_translations_input,
    validate_select_value_translation_languages,
)
from properties.mcp.output_types import EDIT_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
from properties.mcp.types import (
    EditPropertySelectValueInputPayload,
    EditPropertySelectValuesPayload,
    PropertySelectValueTranslationInputPayload,
)
from properties.models import PropertySelectValue


class EditPropertySelectValuesMcpTool(BaseMcpTool):
    name = "edit_property_select_values"
    title = "Edit Property Select Values"
    tags = tool_tags(TAG_EDIT, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
    output_schema = EDIT_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 50

    async def execute(
        self,
        select_values: Annotated[
            list[EditPropertySelectValueInputPayload] | EditPropertySelectValueInputPayload | str,
            Field(
                description=(
                    "One select-value update object or an array of select-value update objects. "
                    "Supports up to 50 select values per call. Use a single object for one select value or an array for bulk updates. "
                    "Each item requires select_value_id and translations:[{language, value}] with at least one translation entry."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Edit translations for one or more existing property select values.

        Pass `select_values` as either a single object or an array of objects. A single object is normalized
        to a one-item batch, and the response always returns an array in `results`.

        Limits:
        - up to 50 select values per call

        Update item shape:
        - `select_value_id`
        - `translations: [{language, value}]`
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            raw_items = self.normalize_bulk_input(
                value=select_values,
                field_name="select_values",
                maximum=self.maximum_items,
            )
            sanitized_values = [
                self._sanitize_select_value_item(
                    select_value=item,
                    multi_tenant_company=multi_tenant_company,
                )
                for item in raw_items
            ]
            await ctx.info(
                f"Editing {len(sanitized_values)} select value(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"select_values": sanitized_values},
                total_records=len(sanitized_values),
            )
            response_data = await self._edit_property_select_values(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                select_values=sanitized_values,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} select-value update request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Edit property select values failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_translations(
        self,
        *,
        translations: list[PropertySelectValueTranslationInputPayload] | str | None,
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
            raise McpToolError("Each select value update must provide at least one translation.")

        return sanitized_translations

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

    def _sanitize_select_value_item(
        self,
        *,
        select_value: dict[str, Any],
        multi_tenant_company,
    ) -> EditPropertySelectValueInputPayload:
        sanitized_select_value_id = self.sanitize_optional_int(
            value=select_value.get("select_value_id"),
            field_name="select_value_id",
            minimum=1,
        )
        if sanitized_select_value_id is None:
            raise McpToolError("Each select value update must provide select_value_id.")

        sanitized_translations = self._sanitize_translations(
            translations=select_value.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )
        return {
            "select_value_id": sanitized_select_value_id,
            "translations": sanitized_translations,
        }

    @database_sync_to_async
    def _edit_property_select_values(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        tool_run_id: int,
        select_values: list[EditPropertySelectValueInputPayload],
    ) -> EditPropertySelectValuesPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []

        try:
            for index, select_value_data in enumerate(select_values, start=1):
                select_value_instance = self._get_select_value(
                    multi_tenant_company=multi_tenant_company,
                    select_value_id=select_value_data["select_value_id"],
                )
                import_instance = ImportPropertySelectValueInstance(
                    {
                        "value": select_value_instance.value,
                        "translations": select_value_data["translations"],
                    },
                    import_process=tool_run,
                    property=select_value_instance.property,
                    instance=select_value_instance,
                )
                import_instance.process()
                results.append(
                    build_select_value_mutation_payload(
                        select_value=select_value_instance,
                        created=False,
                    )
                )
                self.update_mcp_tool_run_progress(
                    tool_run=tool_run,
                    processed_records=index,
                    total_records=len(select_values),
                )
        except Exception as error:
            self.fail_mcp_tool_run(tool_run=tool_run, error=error)
            raise

        response = self.build_bulk_response(
            requested_count=len(select_values),
            processed_count=len(results),
            updated_count=len(results),
            results=results,
        )
        self.complete_mcp_tool_run(
            tool_run=tool_run,
            response_content=response,
            processed_records=len(results),
        )
        return response
