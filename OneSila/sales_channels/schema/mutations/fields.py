from sales_channels.schema.mutations.mutation_classes import ResyncSalesChannelAssignMutation, \
    RefreshSalesChannelWebsiteModelsMutation
from sales_channels.schema.types.input import SalesChannelViewAssignPartialInput, SalesChannelPartialInput


def resync_sales_channel_assign():
    extensions = []
    return ResyncSalesChannelAssignMutation(SalesChannelViewAssignPartialInput, extensions=extensions)

def refresh_website_models_mutation():
    extensions = []
    return RefreshSalesChannelWebsiteModelsMutation(SalesChannelPartialInput, extensions=extensions)