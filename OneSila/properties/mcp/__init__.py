from properties.mcp.tools import (
    CreatePropertiesMcpTool,
    CreatePropertySelectValuesMcpTool,
    EditPropertiesMcpTool,
    EditPropertySelectValuesMcpTool,
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
    CreatePropertiesMcpTool(mcp=mcp)
    EditPropertiesMcpTool(mcp=mcp)
    CreatePropertySelectValuesMcpTool(mcp=mcp)
    EditPropertySelectValuesMcpTool(mcp=mcp)


__all__ = [
    "CreatePropertiesMcpTool",
    "CreatePropertySelectValuesMcpTool",
    "EditPropertiesMcpTool",
    "EditPropertySelectValuesMcpTool",
    "GetPropertyMcpTool",
    "GetPropertySelectValueMcpTool",
    "SearchPropertiesMcpTool",
    "SearchPropertySelectValuesMcpTool",
    "register_property_mcp_tools",
]
