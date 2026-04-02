from properties.mcp.tools import GetPropertyMcpTool, SearchPropertiesMcpTool


def register_property_mcp_tools(*, mcp):
    SearchPropertiesMcpTool(mcp=mcp)
    GetPropertyMcpTool(mcp=mcp)


__all__ = [
    "GetPropertyMcpTool",
    "SearchPropertiesMcpTool",
    "register_property_mcp_tools",
]
