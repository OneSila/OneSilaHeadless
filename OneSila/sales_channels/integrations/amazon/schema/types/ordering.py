from typing import Optional

from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProduct,
    AmazonProductProperty,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonSalesChannelImport,
    AmazonDefaultUnitConfigurator,
    AmazonRemoteLog,
    AmazonSalesChannelView,
    AmazonProductIssue,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
    AmazonExternalProductId,
    AmazonGtinExemption,
    AmazonVariationTheme,
    AmazonImportBrokenRecord,
)
from properties.schema.types.ordering import ProductPropertyOrder
from products.schema.types.ordering import ProductOrder
from imports_exports.schema.types.ordering import ImportOrder


@order(AmazonSalesChannel)
class AmazonSalesChannelOrder:
    id: auto


@order(AmazonProperty)
class AmazonPropertyOrder:
    id: auto


@order(AmazonProduct)
class AmazonProductOrder:
    id: auto


@order(AmazonProductType)
class AmazonProductTypeOrder:
    id: auto


@order(AmazonProductTypeItem)
class AmazonProductTypeItemOrder:
    id: auto


@order(AmazonSalesChannelImport)
class AmazonSalesChannelImportOrder:
    id: auto


@order(AmazonDefaultUnitConfigurator)
class AmazonDefaultUnitConfiguratorOrder:
    id: auto


@order(AmazonSalesChannelView)
class AmazonSalesChannelViewOrder:
    id: auto
    is_default: auto


@order(AmazonRemoteLog)
class AmazonRemoteLogOrder:
    id: auto


@order(AmazonProductIssue)
class AmazonProductIssueOrder:
    id: auto


@order(AmazonPropertySelectValue)
class AmazonPropertySelectValueOrder:
    id: auto
    marketplace: Optional[AmazonSalesChannelViewOrder]


@order(AmazonProductProperty)
class AmazonProductPropertyOrder:
    id: auto
    local_instance: Optional[ProductPropertyOrder]
    remote_product: Optional[AmazonProductOrder]
    remote_select_value: Optional[AmazonPropertySelectValueOrder]


@order(AmazonBrowseNode)
class AmazonBrowseNodeOrder:
    remote_id: auto
    name: auto
    path_depth: auto


@order(AmazonProductBrowseNode)
class AmazonProductBrowseNodeOrder:
    id: auto
    product: Optional[ProductOrder]


@order(AmazonExternalProductId)
class AmazonExternalProductIdOrder:
    id: auto
    product: Optional[ProductOrder]
    view: Optional[AmazonSalesChannelViewOrder]
    value: auto
    type: auto
    created_asin: auto


@order(AmazonGtinExemption)
class AmazonGtinExemptionOrder:
    id: auto
    product: Optional[ProductOrder]
    view: Optional[AmazonSalesChannelViewOrder]


@order(AmazonVariationTheme)
class AmazonVariationThemeOrder:
    id: auto
    product: Optional[ProductOrder]
    view: Optional[AmazonSalesChannelViewOrder]


@order(AmazonImportBrokenRecord)
class AmazonImportBrokenRecordOrder:
    id: auto
    import_process: Optional[ImportOrder]
