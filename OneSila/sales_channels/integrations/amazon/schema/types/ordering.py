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
)
from properties.schema.types.ordering import ProductPropertyOrder
from products.schema.types.ordering import ProductOrder


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
