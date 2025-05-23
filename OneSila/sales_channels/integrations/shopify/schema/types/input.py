from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.shopify.models import ShopifySalesChannel


@input(ShopifySalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class ShopifySalesChannelInput:
    pass


@partial(ShopifySalesChannel, fields="__all__")
class ShopifySalesChannelPartialInput(NodeInput):
    pass
