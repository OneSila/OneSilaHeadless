from __future__ import annotations

from typing import Annotated, Any

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from imports_exports.factories.properties import ImportPropertyInstance
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_EDIT, TAG_PROPERTIES, tool_tags
from llm.models import McpToolRun
from properties.mcp.helpers import (
    build_property_mutation_payload,
    sanitize_property_translations_input,
    validate_translation_languages,
)
from properties.mcp.output_types import EDIT_PROPERTIES_OUTPUT_SCHEMA
from properties.mcp.types import EditPropertiesPayload, EditPropertyInputPayload, PropertyTranslationInputPayload
from properties.models import Property


class EditPropertiesMcpTool(BaseMcpTool):
    name = "edit_properties"
    title = "Edit Properties"
    tags = tool_tags(TAG_EDIT, TAG_PROPERTIES)
    output_schema = EDIT_PROPERTIES_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    maximum_items = 25

    async def execute(
        self,
        properties: Annotated[
            list[EditPropertyInputPayload] | EditPropertyInputPayload | str,
            Field(
                description=(
                    "One property update object or an array of property update objects. "
                    "Supports up to 25 properties per call. Use a single object for one property or an array for bulk updates. "
                    "Each item requires property_id or internal_name and at least one editable field: "
                    "is_public_information, add_to_filters, has_image, or translations:[{language, name}]."
                )
            ),
        ] = ...,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Edit one or more existing company-scoped properties.

        Pass `properties` as either a single object or an array of objects. A single object is normalized
        to a one-item batch, and the response always returns an array in `results`.

        Limits:
        - up to 25 properties per call

        Update item shape:
        - target by `property_id` or `internal_name`
        - optional booleans: `is_public_information`, `add_to_filters`, `has_image`
        - optional `translations: [{language, name}]`
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
                f"Editing {len(sanitized_properties)} propertie(s) for company_id={multi_tenant_company.id}."
            )
            tool_run = await self.create_mcp_tool_run(
                multi_tenant_company=multi_tenant_company,
                payload_content={"properties": sanitized_properties},
                total_records=len(sanitized_properties),
            )
            response_data = await self._edit_properties(
                multi_tenant_company=multi_tenant_company,
                tool_run_id=tool_run.id,
                properties=sanitized_properties,
            )
            return self.build_result(
                summary=f"Processed {response_data['processed_count']} property update request(s).",
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Edit properties failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_translations(
        self,
        *,
        translations: list[PropertyTranslationInputPayload] | str | None,
        multi_tenant_company: MultiTenantCompany,
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

    def _get_property_match(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        internal_name: str | None,
    ) -> Property:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if not any([property_id is not None, internal_name]):
            raise McpToolError("Each property update must provide property_id or internal_name.")

        if property_id is not None:
            queryset = queryset.filter(id=property_id)
        if internal_name:
            queryset = queryset.filter(internal_name__iexact=internal_name)

        property_ids = list(queryset.order_by("id").values_list("id", flat=True).distinct()[:2])
        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided identifiers.")

        return queryset.get(id=property_ids[0])

    def _sanitize_property_item(
        self,
        *,
        property_data: dict[str, Any],
        multi_tenant_company,
    ) -> EditPropertyInputPayload:
        sanitized_property_id = self.sanitize_optional_int(
            value=property_data.get("property_id"),
            field_name="property_id",
            minimum=1,
        )
        sanitized_internal_name = self._sanitize_optional_string(value=property_data.get("internal_name"))
        sanitized_is_public_information = self.sanitize_optional_bool(
            value=property_data.get("is_public_information"),
            field_name="is_public_information",
        )
        sanitized_add_to_filters = self.sanitize_optional_bool(
            value=property_data.get("add_to_filters"),
            field_name="add_to_filters",
        )
        sanitized_has_image = self.sanitize_optional_bool(
            value=property_data.get("has_image"),
            field_name="has_image",
        )
        sanitized_translations = self._sanitize_translations(
            translations=property_data.get("translations"),
            multi_tenant_company=multi_tenant_company,
        )

        if sanitized_property_id is None and not sanitized_internal_name:
            raise McpToolError("Each property update must provide property_id or internal_name.")
        if not any(
            [
                sanitized_is_public_information is not None,
                sanitized_add_to_filters is not None,
                sanitized_has_image is not None,
                sanitized_translations is not None,
            ]
        ):
            raise McpToolError(
                "Each property update must include at least one editable field: is_public_information, add_to_filters, has_image, or translations."
            )

        sanitized_property: EditPropertyInputPayload = {}
        if sanitized_property_id is not None:
            sanitized_property["property_id"] = sanitized_property_id
        if sanitized_internal_name:
            sanitized_property["internal_name"] = sanitized_internal_name
        if sanitized_is_public_information is not None:
            sanitized_property["is_public_information"] = sanitized_is_public_information
        if sanitized_add_to_filters is not None:
            sanitized_property["add_to_filters"] = sanitized_add_to_filters
        if sanitized_has_image is not None:
            sanitized_property["has_image"] = sanitized_has_image
        if sanitized_translations is not None:
            sanitized_property["translations"] = sanitized_translations

        return sanitized_property

    @database_sync_to_async
    def _edit_properties(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        tool_run_id: int,
        properties: list[EditPropertyInputPayload],
    ) -> EditPropertiesPayload:
        tool_run = McpToolRun.objects.get(id=tool_run_id)
        self.start_mcp_tool_run(tool_run=tool_run)
        results = []

        try:
            for index, property_data in enumerate(properties, start=1):
                property_instance = self._get_property_match(
                    multi_tenant_company=multi_tenant_company,
                    property_id=property_data.get("property_id"),
                    internal_name=property_data.get("internal_name"),
                )
                import_payload = {
                    "type": property_instance.type,
                    "is_product_type": property_instance.is_product_type,
                }
                if property_instance.internal_name:
                    import_payload["internal_name"] = property_instance.internal_name
                else:
                    import_payload["name"] = property_instance.name
                if property_data.get("is_public_information") is not None:
                    import_payload["is_public_information"] = property_data["is_public_information"]
                if property_data.get("add_to_filters") is not None:
                    import_payload["add_to_filters"] = property_data["add_to_filters"]
                if property_data.get("has_image") is not None:
                    import_payload["has_image"] = property_data["has_image"]
                if property_data.get("translations") is not None:
                    import_payload["translations"] = property_data["translations"]

                import_instance = ImportPropertyInstance(
                    import_payload,
                    import_process=tool_run,
                    instance=property_instance,
                )
                import_instance.process()
                results.append(
                    build_property_mutation_payload(
                        property_instance=property_instance,
                        created=False,
                    )
                )
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
            updated_count=len(results),
            results=results,
        )
        self.complete_mcp_tool_run(
            tool_run=tool_run,
            response_content=response,
            processed_records=len(results),
        )
        return response
