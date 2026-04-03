from __future__ import annotations

from typing import Annotated

from channels.db import database_sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from core.models.multi_tenant import MultiTenantCompany
from imports_exports.factories.properties import ImportPropertyInstance
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from properties.mcp.helpers import (
    build_import_process,
    get_property_detail_queryset,
    sanitize_property_translations_input,
    serialize_property_detail,
    validate_translation_languages,
)
from properties.mcp.output_types import EDIT_PROPERTY_OUTPUT_SCHEMA
from properties.mcp.types import EditPropertyPayload, PropertyTranslationInputPayload
from properties.models import Property


class EditPropertyMcpTool(BaseMcpTool):
    name = "edit_property"
    title = "Edit Property"
    output_schema = EDIT_PROPERTY_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        property_id: Annotated[int | None, Field(ge=1, description="Exact property database ID.")] = None,
        internal_name: Annotated[str | None, Field(description="Exact property internal name.")] = None,
        is_public_information: Annotated[
            bool | None,
            Field(description="Update whether this property is public information.")
        ] = None,
        add_to_filters: Annotated[
            bool | None,
            Field(description="Update whether this property should be available in filters.")
        ] = None,
        has_image: Annotated[
            bool | None,
            Field(description="Update whether this property expects image-backed select values.")
        ] = None,
        translations: Annotated[
            list[PropertyTranslationInputPayload] | str | None,
            Field(
                description=(
                    "Optional list of translated property names to update or add. "
                    "Translation languages must belong to the authenticated company's enabled languages. "
                    "Use get_company_languages first to see the allowed language codes. "
                    "If the client sends JSON-stringified arguments, a JSON string array is also accepted."
                )
            )
        ] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Edit an existing company-scoped property by exact property ID or exact internal name.
        This tool updates only the supported property fields: public-information flag,
        filter visibility, image support, and translations. Translation entries are upserted,
        so existing languages are updated and new languages are added through the import flow.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_internal_name = self._sanitize_optional_string(value=internal_name)
            translations_payload = self._sanitize_translations(
                translations=translations,
                multi_tenant_company=multi_tenant_company,
            )
            self._validate_update_request(
                is_public_information=is_public_information,
                add_to_filters=add_to_filters,
                has_image=has_image,
                translations=translations_payload,
            )

            await ctx.info(
                f"Editing property for company_id={multi_tenant_company.id} "
                f"with property_id={property_id!r}, internal_name={sanitized_internal_name!r}."
            )

            response_data = await self._edit_property(
                multi_tenant_company=multi_tenant_company,
                property_id=property_id,
                internal_name=sanitized_internal_name,
                is_public_information=is_public_information,
                add_to_filters=add_to_filters,
                has_image=has_image,
                translations=translations_payload,
            )

            await ctx.info(
                f"Updated property_id={response_data['property']['id']} "
                f"internal_name={response_data['property']['internal_name']!r}."
            )

            return self.build_result(
                summary=(
                    f"Updated property '{response_data['property']['name']}' "
                    f"({response_data['property']['type_label']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Edit property failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

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

    def _validate_update_request(
        self,
        *,
        is_public_information: bool | None,
        add_to_filters: bool | None,
        has_image: bool | None,
        translations: list[PropertyTranslationInputPayload] | None,
    ) -> None:
        if not any(
            [
                is_public_information is not None,
                add_to_filters is not None,
                has_image is not None,
                translations is not None,
            ]
        ):
            raise McpToolError(
                "Provide at least one editable field: is_public_information, add_to_filters, has_image, or translations."
            )

    @database_sync_to_async
    def _edit_property(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        internal_name: str | None,
        is_public_information: bool | None,
        add_to_filters: bool | None,
        has_image: bool | None,
        translations: list[PropertyTranslationInputPayload] | None,
    ) -> EditPropertyPayload:
        property_instance = self._get_property_match(
            multi_tenant_company=multi_tenant_company,
            property_id=property_id,
            internal_name=internal_name,
        )
        property_data = self._build_property_data(
            property_instance=property_instance,
            is_public_information=is_public_information,
            add_to_filters=add_to_filters,
            has_image=has_image,
            translations=translations,
        )

        try:
            import_instance = ImportPropertyInstance(
                property_data,
                import_process=build_import_process(multi_tenant_company=multi_tenant_company),
                instance=property_instance,
            )
            import_instance.process()
        except ValueError as error:
            raise McpToolError(str(error)) from error

        property_instance = get_property_detail_queryset(
            multi_tenant_company=multi_tenant_company,
        ).get(id=property_instance.id)

        return {
            "updated": True,
            "property": serialize_property_detail(property_instance=property_instance),
        }

    def _get_property_match(
        self,
        *,
        multi_tenant_company: MultiTenantCompany,
        property_id: int | None,
        internal_name: str | None,
    ) -> Property:
        queryset = Property.objects.filter(multi_tenant_company=multi_tenant_company)

        if not any([property_id is not None, internal_name]):
            raise McpToolError("Provide property_id or internal_name.")

        if property_id is not None:
            queryset = queryset.filter(id=property_id)
        if internal_name:
            queryset = queryset.filter(internal_name__iexact=internal_name)

        property_ids = list(
            queryset.order_by("id").values_list("id", flat=True).distinct()[:2]
        )

        if not property_ids:
            raise McpToolError("Property not found.")
        if len(property_ids) > 1:
            raise McpToolError("Multiple properties matched the provided identifiers.")

        return queryset.get(id=property_ids[0])

    def _build_property_data(
        self,
        *,
        property_instance: Property,
        is_public_information: bool | None,
        add_to_filters: bool | None,
        has_image: bool | None,
        translations: list[PropertyTranslationInputPayload] | None,
    ) -> dict:
        property_data = {
            "type": property_instance.type,
            "is_product_type": property_instance.is_product_type,
        }

        if property_instance.internal_name:
            property_data["internal_name"] = property_instance.internal_name
        else:
            property_data["name"] = property_instance.name

        if is_public_information is not None:
            property_data["is_public_information"] = is_public_information
        if add_to_filters is not None:
            property_data["add_to_filters"] = add_to_filters
        if has_image is not None:
            property_data["has_image"] = has_image
        if translations is not None:
            property_data["translations"] = translations

        return property_data
