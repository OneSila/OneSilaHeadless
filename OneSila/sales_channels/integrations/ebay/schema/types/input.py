from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.ebay.models import EbaySalesChannel


@strawberry_input
class EbayValidateAuthInput:
    code: str
    state: str


@input(EbaySalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class EbaySalesChannelInput:
    pass


@partial(EbaySalesChannel, fields="__all__")
class EbaySalesChannelPartialInput(NodeInput):
    pass
