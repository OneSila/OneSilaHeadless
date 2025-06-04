from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.amazon.models import AmazonSalesChannel


@order(AmazonSalesChannel)
class AmazonSalesChannelOrder:
    id: auto
