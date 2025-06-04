from sales_channels.integrations.amazon.schema.types.input import AmazonSalesChannelInput, AmazonSalesChannelPartialInput
from sales_channels.integrations.amazon.schema.types.types import AmazonSalesChannelType
from core.schema.core.mutations import create, type, List, update


@type(name="Mutation")
class AmazonSalesChannelMutation:
    create_amazon_sales_channel: AmazonSalesChannelType = create(AmazonSalesChannelInput)
    create_amazon_sales_channels: List[AmazonSalesChannelType] = create(AmazonSalesChannelInput)

    update_amazon_sales_channel: AmazonSalesChannelType = update(AmazonSalesChannelPartialInput)
