from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from imports_exports.factories.properties import ImportPropertyInstance
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_CREATE, TAG_PROPERTIES, tool_tags
from properties.mcp.helpers import (
    build_import_process,
    get_property_detail_queryset,
    sanitize_property_translations_input,
    serialize_property_detail,
    validate_translation_languages,
)
from properties.mcp.output_types import CREATE_PROPERTY_OUTPUT_SCHEMA
from properties.mcp.types import CreatePropertyPayload, PropertyTranslationInputPayload, PropertyTypeValue
from properties.models import Property


class CreatePropertyMcpTool(BaseMcpTool):
    name = "create_property"
    title = "Create Property"
    tags = tool_tags(TAG_CREATE, TAG_PROPERTIES)
    output_schema = CREATE_PROPERTY_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        type: Annotated[
            PropertyTypeValue,
            Field(
                description=(
                    "Exact OneSila property type. This is required before creation. "
                    "If you are unsure, call recommend_property_type first."
                )
            ),
        ] = ...,
        name: Annotated[str | None, Field(description="Human-facing property name. Provide this or internal_name.")] = None,
        internal_name: Annotated[str | None, Field(description="Internal property name. Provide this or name.")] = None,
        is_public_information: Annotated[
            bool,
            Field(description="Whether this property is public information.")
        ] = True,
        add_to_filters: Annotated[
            bool,
            Field(description="Whether this property should be available in filters.")
        ] = True,
        has_image: Annotated[
            bool,
            Field(description="Whether this property expects image-backed select values.")
        ] = False,
        is_product_type: Annotated[
            bool,
            Field(description="Whether this property is the special product-type property for the company.")
        ] = False,
        translations: Annotated[
            list[PropertyTranslationInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of translated property names, each with language and name. "
                    "Translation languages must belong to the authenticated company's enabled languages. "
                    "Use get_company_languages first to see the allowed language codes. "
                    "If the client sends JSON-stringified arguments, a JSON string array is also accepted."
                )
            )
        ] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Create or update a company-scoped property using the existing import factory flow.
        This tool requires an explicit property type. If the correct type is unclear,
        call `recommend_property_type` first and confirm the recommendation before creating.

        The import flow will reuse an existing property when the identifiers already match,
        or create a new one when no matching property exists.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_name = self._sanitize_optional_string(value=name)
            sanitized_internal_name = self._sanitize_optional_string(value=internal_name)
            property_type = self._sanitize_type(type=type)
            translations_payload = self._sanitize_translations(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )

            await ctx.info(
                f"Creating property for company_id={multi_tenant_company.id} "
                f"with internal_name={sanitized_internal_name!r}, name={sanitized_name!r}, type={property_type!r}."
            )

            response_data = await self._create_property(
                multi_tenant_company=multi_tenant_company,
                name=sanitized_name,
                internal_name=sanitized_internal_name,
                property_type=property_type,
                is_public_information=is_public_information,
                add_to_filters=add_to_filters,
                has_image=has_image,
                is_product_type=is_product_type,
                translations=translations_payload,
            )

            action = "Created" if response_data["created"] else "Updated existing"
            await ctx.info(
                f"{action} property_id={response_data['property']['id']} "
                f"internal_name={response_data['property']['internal_name']!r}."
            )

            return self.build_result(
                summary=(
                    f"{action} property '{response_data['property']['name']}' "
                    f"({response_data['property']['type_label']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Create property failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _sanitize_type(self, *, type: PropertyTypeValue) -> PropertyTypeValue:
        allowed_types = {choice[0] for choice in Property.TYPES.ALL}
        if type not in allowed_types:
            raise McpToolError(f"Invalid type: {type!r}. Allowed types are: {sorted(allowed_types)}")
        return type

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

    @database_sync_to_async
    def _create_property(
        self,
        *,
        multi_tenant_company,
        name: str | None,
        internal_name: str | None,
        property_type: PropertyTypeValue,
        is_public_information: bool,
        add_to_filters: bool,
        has_image: bool,
        is_product_type: bool,
        translations: list[PropertyTranslationInputPayload] | None,
    ) -> CreatePropertyPayload:
        property_data = self._build_property_data(
            name=name,
            internal_name=internal_name,
            property_type=property_type,
            is_public_information=is_public_information,
            add_to_filters=add_to_filters,
            has_image=has_image,
            is_product_type=is_product_type,
            translations=translations,
        )

        try:
            import_instance = ImportPropertyInstance(
                property_data,
                import_process=build_import_process(multi_tenant_company=multi_tenant_company),
            )
            import_instance.process()
        except ValueError as error:
            raise McpToolError(str(error)) from error

        property_instance = get_property_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=import_instance.instance.id)

        return {
            "created": bool(getattr(import_instance, "created", False)),
            "property": serialize_property_detail(property_instance=property_instance),
        }

    def _build_property_data(
        self,
        *,
        name: str | None,
        internal_name: str | None,
        property_type: PropertyTypeValue,
        is_public_information: bool,
        add_to_filters: bool,
        has_image: bool,
        is_product_type: bool,
        translations: list[PropertyTranslationInputPayload] | None,
    ) -> dict:
        if not any([name, internal_name]):
            raise McpToolError("Provide name or internal_name to create a property.")

        property_data = {
            "type": property_type,
            "is_public_information": is_public_information,
            "add_to_filters": add_to_filters,
            "has_image": has_image,
            "is_product_type": is_product_type,
        }

        if name:
            property_data["name"] = name
        if internal_name:
            property_data["internal_name"] = internal_name
        if translations:
            property_data["translations"] = translations

        return property_data
