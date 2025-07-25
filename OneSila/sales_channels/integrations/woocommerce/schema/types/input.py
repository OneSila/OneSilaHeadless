from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel


@input(WoocommerceSalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class WoocommerceSalesChannelInput:
    pass


@partial(WoocommerceSalesChannel, fields="__all__")
class WoocommerceSalesChannelPartialInput(NodeInput):
    pass
