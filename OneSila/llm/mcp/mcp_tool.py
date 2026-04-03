from __future__ import annotations

import inspect
import logging
from typing import Any

from llm.mcp.auth import get_authenticated_company
from llm.mcp.serializers import json_response


logger = logging.getLogger(__name__)


class McpToolError(Exception):
    pass


class BaseMcpTool:
    name: str | None = None
    description: str | None = None
    read_only: bool = False

    def __init__(self, *, mcp):
        self.mcp = mcp
        self._register_tool()

    def _register_tool(self):
        description = self.description or inspect.getdoc(self.execute) or ""
        return self.mcp.tool(
            name=self.name or self.execute.__name__,
            description=description,
            annotations={"readOnlyHint": self.read_only},
        )(self.execute)

    def execute(self, *args, **kwargs):
        raise NotImplementedError

    def get_multi_tenant_company(self, *, required: bool = True):
        multi_tenant_company = get_authenticated_company()
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

    def handle_error(self, *, error: Exception, action: str) -> str:
        logger.exception("%s error: %s", action, error)
        return json_response(data={"error": str(error)})

    def handle_validation_error(self, *, errors: list[str]) -> str:
        return json_response(data={"errors": errors})
