from __future__ import annotations

from typing import Annotated, Any

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from imports_exports.factories.properties import ImportPropertyInstance
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CREATE, TAG_PROPERTIES, tool_tags
from llm.models import McpToolRun
from properties.mcp.helpers import (
    build_property_mutation_payload,
    sanitize_property_translations_input,
    validate_translation_languages,
)
from properties.mcp.output_types import CREATE_PROPERTIES_OUTPUT_SCHEMA
from properties.mcp.types import (
    CreatePropertiesPayload,
    CreatePropertyInputPayload,
    PropertyTranslationInputPayload,
    PropertyTypeValue,
)
from properties.models import Property


class CreatePropertiesMcpTool(BaseMcpTool):
    name = "create_properties"
    title = "Create Properties"
    tags = tool_tags(TAG_CREATE, TAG_PROPERTIES)
    output_schema = CREATE_PROPERTIES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 25

    async def execute(
        self,
        properties: Annotated[
            list[CreatePropertyInputPayload] | CreatePropertyInputPayload | str,
            Field(
                description=(
                    "One property object or an array of property objects to create. "
                    "Supports up to 25 properties per call. Use a single object for one property or an array for bulk creation. "
                    "Each item requires type and either name or internal_name. Optional fields are is_public_information, add_to_filters, has_image, is_product_type, "
                    "and translations:[{language, name}]."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create one or more company-scoped properties.

        Pass `properties` as either a single object or an array of objects. A single object is normalized
        to a one-item batch, and the response always returns an array in `results`.

        Limits:
        - up to 25 properties per call

        The caller must infer the best property type from the user context and confirm it when there is ambiguity.

        Create item shape:
        - `type`: INT, FLOAT, TEXT, DESCRIPTION, BOOLEAN, DATE, DATETIME, SELECT, or MULTISELECT
        - `name` or `internal_name`
        - optional `translations: [{language, name}]`
        - optional booleans: `is_public_information`, `add_to_filters`, `has_image`, `is_product_type`
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            raw_items = self.normalize_bulk_input(
                value=properties,
                field_name="properties",
                maximum=self.maximum_items,
            )
            sanitized_properties = [
                self._sanitize_property_item(
                    property_data=item,
                    multi_tenant_company=multi_tenant_company,
                )
                for item in raw_items
            ]
            await ctx.info(
                f"Creating {len(sanitized_properties)} propertie(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"properties": sanitized_properties},
                total_records=len(sanitized_properties),
                create_only=True,
            )
            response_data = await self._create_properties(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                properties=sanitized_properties,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} property create request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create properties failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_type(self, *, value) -> PropertyTypeValue:
        allowed_types = {choice[0] for choice in Property.TYPES.ALL}
        if not isinstance(value, str):
            raise McpToolError(f"type must be a string, got: {value!r}")
        normalized_value = value.strip().upper()
        if normalized_value not in allowed_types:
            raise McpToolError(f"Invalid type: {value!r}. Allowed types are: {sorted(allowed_types)}")
        return normalized_value  # type: ignore[return-value]

    def _sanitize_translations(
        self,
        *,
        translations: list[PropertyTranslationInputPayload] | str | None,
        multi_tenant_company,
    ) -> list[PropertyTranslationInputPayload] | None:
        try:
            sanitized_translations = sanitize_property_translations_input(translations=translations)
            validate_translation_languages(
                translations=sanitized_translations,
                multi_tenant_company=multi_tenant_company,
            )
            return sanitized_translations
        except ValueError as error:
            raise McpToolError(str(error)) from error

    def _sanitize_property_item(
        self,
        *,
        property_data: dict[str, Any],
        multi_tenant_company,
    ) -> CreatePropertyInputPayload:
        property_type = self._sanitize_type(value=property_data.get("type"))
        sanitized_name = self._sanitize_optional_string(value=property_data.get("name"))
        sanitized_internal_name = self._sanitize_optional_string(value=property_data.get("internal_name"))
        if not any([sanitized_name, sanitized_internal_name]):
            raise McpToolError("Each property must provide name or internal_name.")

        sanitized_translations = self._sanitize_translations(
            translations=property_data.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )
        is_public_information = property_data.get("is_public_information", True)
        add_to_filters = property_data.get("add_to_filters", True)
        has_image = property_data.get("has_image", False)
        is_product_type = property_data.get("is_product_type", False)

        if not isinstance(is_public_information, bool):
            raise McpToolError(f"is_public_information must be a boolean, got: {is_public_information!r}")
        if not isinstance(add_to_filters, bool):
            raise McpToolError(f"add_to_filters must be a boolean, got: {add_to_filters!r}")
        if not isinstance(has_image, bool):
            raise McpToolError(f"has_image must be a boolean, got: {has_image!r}")
        if not isinstance(is_product_type, bool):
            raise McpToolError(f"is_product_type must be a boolean, got: {is_product_type!r}")

        sanitized_property: CreatePropertyInputPayload = {
            "type": property_type,
            "is_public_information": is_public_information,
            "add_to_filters": add_to_filters,
            "has_image": has_image,
            "is_product_type": is_product_type,
        }
        if sanitized_name:
            sanitized_property["name"] = sanitized_name
        if sanitized_internal_name:
            sanitized_property["internal_name"] = sanitized_internal_name
        if sanitized_translations:
            sanitized_property["translations"] = sanitized_translations
        return sanitized_property

    @database_sync_to_async
    def _create_properties(
        self,
        *,
        multi_tenant_company,
        tool_run_id: int,
        properties: list[CreatePropertyInputPayload],
    ) -> CreatePropertiesPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []
        created_count = 0
        updated_existing_count = 0

        try:
            for index, property_data in enumerate(properties, start=1):
                import_instance = ImportPropertyInstance(
                    property_data,
                    import_process=tool_run,
                )
                import_instance.process()
                result = build_property_mutation_payload(
                    property_instance=import_instance.instance,
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
                    total_records=len(properties),
                )
        except Exception as error:
            self.fail_mcp_tool_run(tool_run=tool_run, error=error)
            raise

        response = self.build_bulk_response(
            requested_count=len(properties),
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
