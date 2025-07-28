from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.ebay.models import EbaySalesChannel


@order(EbaySalesChannel)
class EbaySalesChannelOrder:
    id: auto
