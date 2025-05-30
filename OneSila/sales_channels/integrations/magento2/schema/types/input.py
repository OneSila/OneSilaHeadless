from core.schema.core.types.input import NodeInput, input, partial, strawberry_input
from sales_channels.integrations.magento2.models import MagentoSalesChannel


@input(MagentoSalesChannel, exclude=['integration_ptr', 'saleschannel_ptr'])
class MagentoSalesChannelInput:
    pass


@partial(MagentoSalesChannel, fields="__all__")
class MagentoSalesChannelPartialInput(NodeInput):
    pass


@strawberry_input
class MagentoRemoteEanCodeAttributeInput:
    name: str
    attribute_code: str
    sales_channel: MagentoSalesChannelPartialInput
