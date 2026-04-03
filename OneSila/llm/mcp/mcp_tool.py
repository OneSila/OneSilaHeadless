from __future__ import annotations

import inspect
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
            content=[TextContent(type="text", text=summary)],
            structured_content=structured_content,
            meta=meta,
        )
