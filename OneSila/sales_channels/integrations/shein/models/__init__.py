"""Model package for the Shein integration."""

from .categories import SheinCategory, SheinProductCategory
from .properties import (
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinInternalProperty,
    SheinInternalPropertyOption
)

from .sales_channels import (
    SheinRemoteCurrency,
    SheinRemoteLanguage,
    SheinSalesChannel,
    SheinSalesChannelView,
)

from .imports import SheinSalesChannelImport
from .issues import SheinProductIssue
from .products import (
    SheinEanCode,
    SheinImageProductAssociation,
    SheinProduct,
    SheinProductContent,
)

__all__ = [
    "SheinCategory",
    "SheinProductCategory",
    "SheinProductType",
    "SheinProductTypeItem",
    "SheinProperty",
    "SheinPropertySelectValue",
    "SheinInternalProperty",
    "SheinInternalPropertyOption",
    "SheinRemoteCurrency",
    "SheinRemoteLanguage",
    "SheinSalesChannel",
    "SheinSalesChannelView",
    "SheinSalesChannelImport",
    "SheinProductIssue",
    "SheinProduct",
    "SheinProductContent",
    "SheinEanCode",
    "SheinImageProductAssociation",
]
