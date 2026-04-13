from products.mcp.tools import (
    ActivateProductMcpTool,
    AddProductImagesMcpTool,
    CreateProductMcpTool,
    DeactivateProductMcpTool,
    GetProductOnesilaUrlMcpTool,
    GetProductMcpTool,
    GetProductTypesMcpTool,
    GetVatRatesMcpTool,
    SearchSalesChannelsMcpTool,
    SearchProductsMcpTool,
    UpdateProductContentMcpTool,
    UpsertProductPriceMcpTool,
    UpsertProductPropertyValuesMcpTool,
)


def register_product_mcp_tools(*, mcp):
    SearchProductsMcpTool(mcp=mcp)
    GetProductMcpTool(mcp=mcp)
    GetProductOnesilaUrlMcpTool(mcp=mcp)
    SearchSalesChannelsMcpTool(mcp=mcp)
    GetProductTypesMcpTool(mcp=mcp)
    GetVatRatesMcpTool(mcp=mcp)
    CreateProductMcpTool(mcp=mcp)
    ActivateProductMcpTool(mcp=mcp)
    DeactivateProductMcpTool(mcp=mcp)
    UpsertProductPriceMcpTool(mcp=mcp)
    AddProductImagesMcpTool(mcp=mcp)
    UpsertProductPropertyValuesMcpTool(mcp=mcp)
    UpdateProductContentMcpTool(mcp=mcp)


__all__ = [
    "ActivateProductMcpTool",
    "AddProductImagesMcpTool",
    "CreateProductMcpTool",
    "DeactivateProductMcpTool",
    "GetProductOnesilaUrlMcpTool",
    "GetProductMcpTool",
    "GetProductTypesMcpTool",
    "GetVatRatesMcpTool",
    "SearchSalesChannelsMcpTool",
    "SearchProductsMcpTool",
    "UpdateProductContentMcpTool",
    "UpsertProductPriceMcpTool",
    "UpsertProductPropertyValuesMcpTool",
    "register_product_mcp_tools",
]
