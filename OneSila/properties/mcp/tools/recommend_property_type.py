from __future__ import annotations

from typing import Annotated

from asgiref.sync import sync_to_async
from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.tools.tool import ToolResult
from pydantic import Field

from llm.factories.property_type_detector import DetectPropertyTypeLLM
from llm.mcp.mcp_tool import BaseMcpTool, McpToolError
from llm.mcp.tags import TAG_PROPERTIES, TAG_RECOMMEND, TAG_TYPES, tool_tags
from properties.mcp.helpers import get_property_type_label
from properties.mcp.output_types import RECOMMEND_PROPERTY_TYPE_OUTPUT_SCHEMA
from properties.mcp.types import PropertyTypeValue, RecommendPropertyTypePayload


class RecommendPropertyTypeMcpTool(BaseMcpTool):
    name = "recommend_property_type"
    title = "Recommend Property Type"
    read_only = True
    tags = tool_tags(TAG_RECOMMEND, TAG_PROPERTIES, TAG_TYPES)
    output_schema = RECOMMEND_PROPERTY_TYPE_OUTPUT_SCHEMA
    annotations = {
        "idempotentHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }

    async def execute(
        self,
        name: Annotated[str | None, Field(description="Human-facing property name, if known.")] = None,
        internal_name: Annotated[str | None, Field(description="Internal property name, if known.")] = None,
        description: Annotated[str | None, Field(description="Optional business description that helps the detector infer the property type.")] = None,
        sample_values: Annotated[list[str] | None, Field(description="Optional sample values that help clarify whether the property is free text, numeric, boolean, single-choice, or multi-choice.")] = None,
        ctx: Context = CurrentContext(),
    ) -> ToolResult:
        """
        Recommend the most likely OneSila property type using the existing LLM-based property-type detector.
        Use this tool before `create_property` when the correct property type is unclear.

        This tool does not create anything. It only returns a recommended type and a human-readable label.
        After user confirmation, call `create_property` with the selected `type`.
        """
        try:
            multi_tenant_company = await self.get_multi_tenant_company(required=True)
            sanitized_name = self._sanitize_optional_string(value=name)
            sanitized_internal_name = self._sanitize_optional_string(value=internal_name)
            payload = self._build_detector_payload(
                name=sanitized_name,
                internal_name=sanitized_internal_name,
                description=description,
                sample_values=sample_values,
            )
            await ctx.info(
                f"Recommending property type for company_id={multi_tenant_company.id} "
                f"with name={sanitized_name!r}, internal_name={sanitized_internal_name!r}."
            )
            recommended_type = await self._detect_property_type(
                payload=payload,
                multi_tenant_company=multi_tenant_company,
            )
            recommended_type_label = get_property_type_label(type_value=recommended_type)
            response_data: RecommendPropertyTypePayload = {
                "recommended_type": recommended_type,
                "recommended_type_label": recommended_type_label,
                "requires_confirmation": True,
                "message": (
                    f"Recommended property type is {recommended_type} "
                    f"({recommended_type_label}). "
                    "Confirm this type before calling create_property."
                ),
                "name": sanitized_name,
                "internal_name": sanitized_internal_name,
            }
            await ctx.info(
                f"Recommended property type {response_data['recommended_type']} for company_id={multi_tenant_company.id}."
            )
            return self.build_result(
                summary=(
                    f"Recommended property type: {response_data['recommended_type_label']} "
                    f"({response_data['recommended_type']})."
                ),
                structured_content=response_data,
            )
        except McpToolError as error:
            await ctx.warning(str(error))
            raise
        except Exception as error:
            await ctx.error(f"Recommend property type failed: {error}")
            self.handle_error(error=error, action=self.name)
            raise

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _build_detector_payload(
        self,
        *,
        name: str | None,
        internal_name: str | None,
        description: str | None,
        sample_values: list[str] | None,
    ) -> dict:
        if not any([name, internal_name]):
            raise McpToolError("Provide name or internal_name to recommend a property type.")

        payload: dict = {}
        if name:
            payload["name"] = name
        if internal_name:
            payload["internal_name"] = internal_name
        if description:
            payload["description"] = description.strip()
        if sample_values:
            if not isinstance(sample_values, list) or not all(isinstance(item, str) for item in sample_values):
                raise McpToolError("sample_values must be a list of strings.")
            payload["sample_values"] = [item.strip() for item in sample_values if item.strip()]

        if sample_values is not None and not payload.get("sample_values"):
            raise McpToolError("sample_values must contain at least one non-empty string when provided.")

        return payload

    @sync_to_async
    def _detect_property_type(
        self,
        *,
        payload: dict,
        multi_tenant_company,
    ) -> PropertyTypeValue:
        llm = DetectPropertyTypeLLM(
            property_data=payload,
            multi_tenant_company=multi_tenant_company,
        )
        detected_type = llm.detect_type()
        return detected_type
