from sales_channels.schema.mutations.mutation_classes import (
    ResyncSalesChannelAssignMutation,
    RefreshSalesChannelWebsiteModelsMutation,
    ResyncSalesChannelGptFeedMutation,
)
from sales_channels.schema.types.input import (
    SalesChannelViewAssignPartialInput,
    SalesChannelPartialInput,
    SalesChannelGptFeedPartialInput,
)


def resync_sales_channel_assign():
    extensions = []
    return ResyncSalesChannelAssignMutation(SalesChannelViewAssignPartialInput, extensions=extensions)


def refresh_website_models_mutation():
    extensions = []
    return RefreshSalesChannelWebsiteModelsMutation(SalesChannelPartialInput, extensions=extensions)


def resync_sales_channel_gpt_feed_mutation():
    extensions = []
    return ResyncSalesChannelGptFeedMutation(SalesChannelGptFeedPartialInput, extensions=extensions)
