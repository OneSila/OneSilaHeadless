from properties.mcp.tools import (
    CreatePropertyMcpTool,
    CreatePropertySelectValueMcpTool,
    EditPropertyMcpTool,
    EditPropertySelectValueMcpTool,
    GetPropertyMcpTool,
    GetPropertySelectValueMcpTool,
    SearchPropertiesMcpTool,
    SearchPropertySelectValuesMcpTool,
)


def register_property_mcp_tools(*, mcp):
    SearchPropertiesMcpTool(mcp=mcp)
    GetPropertyMcpTool(mcp=mcp)
    SearchPropertySelectValuesMcpTool(mcp=mcp)
    GetPropertySelectValueMcpTool(mcp=mcp)
    CreatePropertyMcpTool(mcp=mcp)
    EditPropertyMcpTool(mcp=mcp)
    CreatePropertySelectValueMcpTool(mcp=mcp)
    EditPropertySelectValueMcpTool(mcp=mcp)


__all__ = [
    "CreatePropertyMcpTool",
    "CreatePropertySelectValueMcpTool",
    "EditPropertyMcpTool",
    "EditPropertySelectValueMcpTool",
    "GetPropertyMcpTool",
    "GetPropertySelectValueMcpTool",
    "SearchPropertiesMcpTool",
    "SearchPropertySelectValuesMcpTool",
    "register_property_mcp_tools",
]
