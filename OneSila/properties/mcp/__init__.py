from properties.mcp.tools import (
    CreatePropertyMcpTool,
    CreatePropertySelectValueMcpTool,
    EditPropertyMcpTool,
    EditPropertySelectValueMcpTool,
    GetCompanyLanguagesMcpTool,
    GetPropertyMcpTool,
    GetPropertySelectValueMcpTool,
    RecommendPropertyTypeMcpTool,
    SearchPropertiesMcpTool,
    SearchPropertySelectValuesMcpTool,
)


def register_property_mcp_tools(*, mcp):
    GetCompanyLanguagesMcpTool(mcp=mcp)
    SearchPropertiesMcpTool(mcp=mcp)
    GetPropertyMcpTool(mcp=mcp)
    SearchPropertySelectValuesMcpTool(mcp=mcp)
    GetPropertySelectValueMcpTool(mcp=mcp)
    RecommendPropertyTypeMcpTool(mcp=mcp)
    CreatePropertyMcpTool(mcp=mcp)
    EditPropertyMcpTool(mcp=mcp)
    CreatePropertySelectValueMcpTool(mcp=mcp)
    EditPropertySelectValueMcpTool(mcp=mcp)


__all__ = [
    "CreatePropertyMcpTool",
    "CreatePropertySelectValueMcpTool",
    "EditPropertyMcpTool",
    "EditPropertySelectValueMcpTool",
    "GetCompanyLanguagesMcpTool",
    "GetPropertyMcpTool",
    "GetPropertySelectValueMcpTool",
    "RecommendPropertyTypeMcpTool",
    "SearchPropertiesMcpTool",
    "SearchPropertySelectValuesMcpTool",
    "register_property_mcp_tools",
]
