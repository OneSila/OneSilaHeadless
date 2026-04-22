from products.mcp.resources import register_product_mcp_resources
from products.mcp.tools import (
    CreateProductsMcpTool,
    GetCompanyDetailsMcpTool,
    GetProductMcpTool,
    SearchSalesChannelsMcpTool,
    SearchProductsMcpTool,
    UpsertProductsMcpTool,
)


def register_product_mcp_tools(*, mcp):
    register_product_mcp_resources(mcp=mcp)
    GetCompanyDetailsMcpTool(mcp=mcp)
    SearchProductsMcpTool(mcp=mcp)
    GetProductMcpTool(mcp=mcp)
    SearchSalesChannelsMcpTool(mcp=mcp)
    CreateProductsMcpTool(mcp=mcp)
    UpsertProductsMcpTool(mcp=mcp)


__all__ = [
    "CreateProductsMcpTool",
    "GetCompanyDetailsMcpTool",
    "GetProductMcpTool",
    "SearchSalesChannelsMcpTool",
    "SearchProductsMcpTool",
    "UpsertProductsMcpTool",
    "register_product_mcp_resources",
    "register_product_mcp_tools",
]
