from collections import OrderedDict

from sales_channels.integrations.amazon.models import AmazonSalesChannelView

from .sync import AmazonBrowseNodeSyncFactory


class AmazonBrowseNodeRefreshFactory:
    """Fetch browse nodes for all known marketplaces."""

    def run(self):
        views = (
            AmazonSalesChannelView.objects.filter(remote_id__isnull=False)
            .select_related("sales_channel")
            .order_by("remote_id")
        )
        unique_views = OrderedDict()
        for view in views.iterator():
            unique_views.setdefault(view.remote_id, view)
        for view in unique_views.values():
            fac = AmazonBrowseNodeSyncFactory(view)
            fac.run()
