from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.magento2.models import MagentoSalesChannel


@order(MagentoSalesChannel)
class MagentoSalesChannelOrder:
    id: auto