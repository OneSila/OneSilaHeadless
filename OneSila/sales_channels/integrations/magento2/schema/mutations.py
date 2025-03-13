from sales_channels.integrations.magento2.schema.types.input import MagentoSalesChannelInput, MagentoSalesChannelPartialInput
from sales_channels.integrations.magento2.schema.types.types import MagentoSalesChannelType
from core.schema.core.mutations import create, type, List, update


@type(name="Mutation")
class MagentoSalesChannelMutation:
    create_magento_sales_channel: MagentoSalesChannelType = create(MagentoSalesChannelInput)
    create_magento_sales_channels: List[MagentoSalesChannelType] = create(MagentoSalesChannelInput)

    update_magento_sales_channel: MagentoSalesChannelType = update(MagentoSalesChannelPartialInput)