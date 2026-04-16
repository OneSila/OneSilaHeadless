from __future__ import annotations

import inspect
import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from llm.mcp.auth import get_authenticated_company
from mcp.types import TextContent


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
        structured_content_text = json.dumps(
            structured_content,
            ensure_ascii=True,
            separators=(",", ":"),
            default=str,
        )
        return ToolResult(
            content=[
                TextContent(type="text", text=structured_content_text),
            ],
            meta=meta,
        )
