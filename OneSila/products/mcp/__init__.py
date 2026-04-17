from products.mcp.resources import register_product_mcp_resources
from products.mcp.tools import (
    CreateProductMcpTool,
    GetCompanyDetailsMcpTool,
    GetProductMcpTool,
    SearchSalesChannelsMcpTool,
    SearchProductsMcpTool,
    UpsertProductMcpTool,
)


def register_product_mcp_tools(*, mcp):
    register_product_mcp_resources(mcp=mcp)
    GetCompanyDetailsMcpTool(mcp=mcp)
    SearchProductsMcpTool(mcp=mcp)
    GetProductMcpTool(mcp=mcp)
    SearchSalesChannelsMcpTool(mcp=mcp)
    CreateProductMcpTool(mcp=mcp)
    UpsertProductMcpTool(mcp=mcp)


__all__ = [
    "CreateProductMcpTool",
    "GetCompanyDetailsMcpTool",
    "GetProductMcpTool",
    "SearchSalesChannelsMcpTool",
    "SearchProductsMcpTool",
    "UpsertProductMcpTool",
    "register_product_mcp_resources",
    "register_product_mcp_tools",
]
