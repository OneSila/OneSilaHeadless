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
    TAG_CREATE,
    TAG_PROPERTIES,
    TAG_PROPERTY_SELECT_VALUES,
    tool_tags,
)
from llm.models import McpToolRun
from properties.mcp.helpers import (
    build_select_value_mutation_payload,
    resolve_property_ids,
    sanitize_select_value_translations_input,
    validate_select_value_translation_languages,
)
from properties.mcp.output_types import CREATE_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
from properties.mcp.types import (
    CreatePropertySelectValueInputPayload,
    CreatePropertySelectValuesPayload,
    PropertySelectValueTranslationInputPayload,
)
from properties.models import Property


class CreatePropertySelectValuesMcpTool(BaseMcpTool):
    name = "create_property_select_values"
    title = "Create Property Select Values"
    tags = tool_tags(TAG_CREATE, TAG_PROPERTIES, TAG_PROPERTY_SELECT_VALUES)
    output_schema = CREATE_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 50

    async def execute(
        self,
        select_values: Annotated[
            list[CreatePropertySelectValueInputPayload] | CreatePropertySelectValueInputPayload | str,
            Field(
                description=(
                    "One select-value object or an array of select-value objects to create. "
                    "Supports up to 50 select values per call. Use a single object for one select value or an array for bulk creation. "
                    "Each item requires value and a property identifier: property_id, property_internal_name, or property_name. "
                    "Optional translations are translations:[{language, value}]."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create or reuse one or more property select values.

        Pass `select_values` as either a single object or an array of objects. A single object is normalized
        to a one-item batch, and the response always returns an array in `results`.

        Limits:
        - up to 50 select values per call

        Create item shape:
        - `value`
        - one of `property_id`, `property_internal_name`, or `property_name`
        - optional `translations: [{language, value}]`
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
                f"Creating {len(sanitized_values)} select value(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"select_values": sanitized_values},
                total_records=len(sanitized_values),
            )
            response_data = await self._create_property_select_values(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                select_values=sanitized_values,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} select-value create request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create property select values failed: {error}")
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

    def _sanitize_select_value_item(
        self,
        *,
        select_value: dict[str, Any],
        multi_tenant_company,
    ) -> CreatePropertySelectValueInputPayload:
        sanitized_value = self.validate_required_string(
            value=select_value.get("value"),
            field_name="value",
        )
        sanitized_property_id = self.sanitize_optional_int(
            value=select_value.get("property_id"),
            field_name="property_id",
            minimum=1,
        )
        sanitized_property_internal_name = self._sanitize_optional_string(
            value=select_value.get("property_internal_name")
        )
        sanitized_property_name = self._sanitize_optional_string(value=select_value.get("property_name"))
        sanitized_translations = self._sanitize_translations(
            translations=select_value.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )

        if not any([sanitized_property_id is not None, sanitized_property_internal_name, sanitized_property_name]):
            raise McpToolError("Each select value must provide property_id, property_internal_name, or property_name.")

        sanitized_select_value: CreatePropertySelectValueInputPayload = {
            "value": sanitized_value,
        }
        if sanitized_property_id is not None:
            sanitized_select_value["property_id"] = sanitized_property_id
        if sanitized_property_internal_name:
            sanitized_select_value["property_internal_name"] = sanitized_property_internal_name
        if sanitized_property_name:
            sanitized_select_value["property_name"] = sanitized_property_name
        if sanitized_translations is not None:
            sanitized_select_value["translations"] = sanitized_translations
        return sanitized_select_value

    def _resolve_property(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        property_internal_name: str | None,
        property_name: str | None,
    ) -> Property:
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

    @database_sync_to_async
    def _create_property_select_values(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        tool_run_id: int,
        select_values: list[CreatePropertySelectValueInputPayload],
    ) -> CreatePropertySelectValuesPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []
        created_count = 0
        updated_existing_count = 0

        try:
            for index, select_value_data in enumerate(select_values, start=1):
                property_instance = self._resolve_property(
                    multi_tenant_company=multi_tenant_company,
                    property_id=select_value_data.get("property_id"),
                    property_internal_name=select_value_data.get("property_internal_name"),
                    property_name=select_value_data.get("property_name"),
                )
                import_payload = {
                    "value": select_value_data["value"],
                }
                if select_value_data.get("translations") is not None:
                    import_payload["translations"] = select_value_data["translations"]

                import_instance = ImportPropertySelectValueInstance(
                    import_payload,
                    import_process=tool_run,
                    property=property_instance,
                )
                import_instance.process()
                result = build_select_value_mutation_payload(
                    select_value=import_instance.instance,
                    created=bool(getattr(import_instance, "created", False)),
                )
                results.append(result)
                if result["created"]:
                    created_count += 1
                else:
                    updated_existing_count += 1
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
            created_count=created_count,
            updated_existing_count=updated_existing_count,
            results=results,
        )
        self.complete_mcp_tool_run(
            tool_run=tool_run,
            response_content=response,
            processed_records=len(results),
        )
        return response
