from core.schema.core.types.input import NodeInput, input, partial
from sales_channels.integrations.amazon.models import AmazonSalesChannel


@input(AmazonSalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class AmazonSalesChannelInput:
    pass


@partial(AmazonSalesChannel, fields="__all__")
class AmazonSalesChannelPartialInput(NodeInput):
    pass
