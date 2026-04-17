from __future__ import annotations

import inspect
import json
import logging
import traceback
from typing import Any

from channels.db import database_sync_to_async
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from imports_exports.models import Import
from llm.mcp.auth import get_authenticated_company
from llm.models import McpToolRun
logger = logging.getLogger(__name__)


class McpToolError(ToolError):
    pass


class BaseMcpTool:
    name: str | None = None
    title: str | None = None
    description: str | None = None
    read_only: bool = False
    tags: set[str] | None = None
    meta: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    timeout: float | None = None

    def __init__(self, *, mcp):
        self.mcp = mcp
        self._register_tool()

    def _register_tool(self):
        description = self.description or inspect.getdoc(self.execute) or ""
        return self.mcp.tool(
            name=self.name or self.execute.__name__,
            title=self.title,
            description=description,
            tags=self.tags,
            meta=self.meta,
            annotations=self._build_annotations(),
            output_schema=self.output_schema,
            timeout=self.timeout,
        )(self.execute)

    def execute(self, *args, **kwargs):
        raise NotImplementedError

    def _build_annotations(self) -> dict[str, Any]:
        annotations = {"readOnlyHint": self.read_only}
        if self.annotations:
            annotations.update(self.annotations)
        if self.title and "title" not in annotations:
            annotations["title"] = self.title
        return annotations

    async def get_multi_tenant_company(self, *, required: bool = True):
        multi_tenant_company = await database_sync_to_async(get_authenticated_company)()
        if multi_tenant_company is None and required:
            raise McpToolError("Could not determine the authenticated company.")
        return multi_tenant_company

    def validate_required_string(self, *, value: str | None, field_name: str):
        if not value or not value.strip():
            raise McpToolError(f"{field_name} is required and cannot be empty.")
        return value.strip()

    def validate_identifier(self, *, value: Any, field_name: str):
        if value is None:
            raise McpToolError(f"{field_name} is required.")
        return value

    def sanitize_limit(self, *, limit: int, maximum: int = 100) -> int:
        if not isinstance(limit, int) or limit < 1:
            raise McpToolError(f"limit must be a positive integer, got: {limit!r}")
        return min(limit, maximum)

    def sanitize_offset(self, *, offset: int) -> int:
        if not isinstance(offset, int) or offset < 0:
            raise McpToolError(f"offset must be a non-negative integer, got: {offset!r}")
        return offset

    def sanitize_optional_bool(self, *, value: bool | None, field_name: str) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise McpToolError(f"{field_name} must be a boolean, got: {value!r}")
        return value

    def sanitize_optional_string(self, *, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _sanitize_optional_string(self, *, value: str | None) -> str | None:
        return self.sanitize_optional_string(value=value)

    def sanitize_optional_int(
        self,
        *,
        value: int | None,
        field_name: str,
        minimum: int | None = None,
    ) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int):
            raise McpToolError(f"{field_name} must be an integer, got: {value!r}")
        if minimum is not None and value < minimum:
            raise McpToolError(f"{field_name} must be >= {minimum}, got: {value!r}")
        return value

    def normalize_bulk_input(
        self,
        *,
        value,
        field_name: str,
        maximum: int,
    ) -> list[dict[str, Any]]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise McpToolError(
                    f"{field_name} must be an object, a list of objects, or a JSON string encoding one of those shapes."
                ) from error

        if isinstance(value, dict):
            items = [value]
        elif isinstance(value, list):
            items = value
        else:
            raise McpToolError(
                f"{field_name} must be an object, a list of objects, or a JSON string encoding one of those shapes."
            )

        if not items:
            raise McpToolError(f"{field_name} must contain at least one item.")
        if len(items) > maximum:
            raise McpToolError(
                f"{field_name} supports up to {maximum} items per call; received {len(items)}."
            )
        if not all(isinstance(item, dict) for item in items):
            raise McpToolError(f"Each entry in {field_name} must be an object.")

        return items

    async def create_mcp_tool_run(
        self,
        *,
        multi_tenant_company,
        payload_content: dict[str, Any],
        total_records: int,
        create_only: bool = False,
        update_only: bool = False,
        override_only: bool = False,
        skip_broken_records: bool = False,
    ) -> McpToolRun:
        return await database_sync_to_async(self._create_mcp_tool_run)(
            multi_tenant_company=multi_tenant_company,
            payload_content=payload_content,
            total_records=total_records,
            create_only=create_only,
            update_only=update_only,
            override_only=override_only,
            skip_broken_records=skip_broken_records,
        )

    def _create_mcp_tool_run(
        self,
        *,
        multi_tenant_company,
        payload_content: dict[str, Any],
        total_records: int,
        create_only: bool,
        update_only: bool,
        override_only: bool,
        skip_broken_records: bool,
    ) -> McpToolRun:
        return McpToolRun.objects.create(
            multi_tenant_company=multi_tenant_company,
            tool_name=self.name or self.execute.__name__,
            payload_content=payload_content,
            total_records=total_records,
            processed_records=0,
            percentage=0,
            create_only=create_only,
            update_only=update_only,
            override_only=override_only,
            skip_broken_records=skip_broken_records,
            status=Import.STATUS_NEW,
        )

    def start_mcp_tool_run(self, *, tool_run: McpToolRun) -> None:
        tool_run.status = Import.STATUS_PROCESSING
        tool_run.percentage = 0
        tool_run.processed_records = 0
        tool_run.broken_records = []
        tool_run.error_traceback = ""
        tool_run.save(
            update_fields=[
                "status",
                "percentage",
                "processed_records",
                "broken_records",
                "error_traceback",
                "updated_at",
            ]
        )

    def update_mcp_tool_run_progress(
        self,
        *,
        tool_run: McpToolRun,
        processed_records: int,
        total_records: int,
    ) -> None:
        safe_total = max(1, total_records)
        percentage = min(100, int((processed_records / safe_total) * 100))
        tool_run.processed_records = processed_records
        tool_run.percentage = percentage
        tool_run.save(update_fields=["processed_records", "percentage", "updated_at"])

    def complete_mcp_tool_run(
        self,
        *,
        tool_run: McpToolRun,
        response_content: dict[str, Any],
        processed_records: int,
        assigned_view_ids: list[int] | None = None,
    ) -> None:
        tool_run.status = Import.STATUS_SUCCESS
        tool_run.percentage = 100
        tool_run.processed_records = processed_records
        tool_run.response_content = response_content
        tool_run.save(
            update_fields=[
                "status",
                "percentage",
                "processed_records",
                "response_content",
                "updated_at",
            ]
        )
        if assigned_view_ids is not None:
            tool_run.assigned_views.set(assigned_view_ids)

    def fail_mcp_tool_run(self, *, tool_run: McpToolRun, error: Exception) -> None:
        tool_run.status = Import.STATUS_FAILED
        tool_run.percentage = 100
        tool_run.error_traceback = traceback.format_exc()
        tool_run.save(update_fields=["status", "percentage", "error_traceback", "updated_at"])

    def build_bulk_response(
        self,
        *,
        requested_count: int,
        processed_count: int,
        results: list[dict[str, Any]],
        **summary_counts: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "requested_count": requested_count,
            "processed_count": processed_count,
            "results": results,
        }
        payload.update(summary_counts)
        return payload

    def handle_error(self, *, error: Exception, action: str) -> None:
        logger.exception("%s error: %s", action, error)
        if isinstance(error, McpToolError):
            raise error
        raise ToolError(f"Unexpected error while running {action}.") from error

    def build_result(
        self,
        *,
        summary: str,
        structured_content: dict[str, Any],
        meta: dict[str, Any] | None = None,
    ) -> ToolResult:
        return ToolResult(
            content=[],
            structured_content=structured_content,
            meta=meta,
        )
