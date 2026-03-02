"""Model package for the Shein integration."""

from .categories import SheinCategory, SheinProductCategoryOld, SheinProductCategory
from .properties import (
    SheinProductType,
    SheinProductTypeItem,
    SheinProperty,
    SheinPropertySelectValue,
    SheinProductProperty,
    SheinInternalProperty,
    SheinInternalPropertyOption
)

from .sales_channels import (
    SheinRemoteCurrency,
    SheinRemoteLanguage,
    SheinSalesChannel,
    SheinSalesChannelView,
)

from .prices import SheinPrice
from .imports import SheinSalesChannelImport
from .issues import SheinProductIssue
from .products import (
    SheinEanCode,
    SheinImageProductAssociation,
    SheinProduct,
    SheinProductContent,
)
from .documents import SheinDocument, SheinDocumentThroughProduct, SheinDocumentType

__all__ = [
    "SheinCategory",
    "SheinProductCategory",
    "SheinProductCategoryOld",
    "SheinProductType",
    "SheinProductTypeItem",
    "SheinProperty",
    "SheinPropertySelectValue",
    "SheinProductProperty",
    "SheinInternalProperty",
    "SheinInternalPropertyOption",
    "SheinRemoteCurrency",
    "SheinRemoteLanguage",
    "SheinSalesChannel",
    "SheinSalesChannelView",
    "SheinPrice",
    "SheinSalesChannelImport",
    "SheinProductIssue",
    "SheinProduct",
    "SheinProductContent",
    "SheinEanCode",
    "SheinImageProductAssociation",
    "SheinDocumentType",
    "SheinDocument",
    "SheinDocumentThroughProduct",
]
