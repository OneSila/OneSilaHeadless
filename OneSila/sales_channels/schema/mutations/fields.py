from sales_channels.schema.mutations.mutation_classes import ResyncSalesChannelAssignMutation
from sales_channels.schema.types.input import SalesChannelViewAssignPartialInput


def resync_sales_channel_assign():
    extensions = []
    return ResyncSalesChannelAssignMutation(SalesChannelViewAssignPartialInput, extensions=extensions)