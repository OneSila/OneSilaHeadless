from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonProperty,
    AmazonPropertySelectValue,
    AmazonProductType,
    AmazonProductTypeItem,
    AmazonSalesChannelImport,
    AmazonDefaultUnitConfigurator,
    AmazonRemoteLog,
)


@order(AmazonSalesChannel)
class AmazonSalesChannelOrder:
    id: auto


@order(AmazonProperty)
class AmazonPropertyOrder:
    id: auto


@order(AmazonPropertySelectValue)
class AmazonPropertySelectValueOrder:
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


@order(AmazonRemoteLog)
class AmazonRemoteLogOrder:
    id: auto
