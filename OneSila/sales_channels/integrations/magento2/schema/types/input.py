from core.schema.core.types.input import NodeInput, input, partial
from sales_channels.integrations.magento2.models import MagentoSalesChannel


@input(MagentoSalesChannel,  exclude=['integration_ptr', 'saleschannel_ptr'])
class MagentoSalesChannelInput:
    pass

@partial(MagentoSalesChannel, fields="__all__")
class MagentoSalesChannelPartialInput(NodeInput):
    pass