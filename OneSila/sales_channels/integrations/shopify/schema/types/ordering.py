from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.shopify.models import ShopifySalesChannel


@order(ShopifySalesChannel)
class ShopifySalesChannelOrder:
    id: auto