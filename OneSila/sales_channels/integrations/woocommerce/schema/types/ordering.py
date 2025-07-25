from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


@order(WoocommerceSalesChannel)
class WoocommerceSalesChannelOrder:
    id: auto
