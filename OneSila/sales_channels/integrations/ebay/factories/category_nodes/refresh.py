from __future__ import annotations

from collections import OrderedDict

from sales_channels.integrations.ebay.models import EbaySalesChannelView

from .sync import EbayCategoryNodeSyncFactory


class EbayCategoryNodeRefreshFactory:
    """Fetch eBay category nodes for all marketplaces once."""

    def run(self) -> None:
        views = (
            EbaySalesChannelView.objects.filter(
                sales_channel__active=True,
                default_category_tree_id__isnull=False,
            )
            .exclude(default_category_tree_id="")
            .select_related("sales_channel")
            .order_by("default_category_tree_id")
        )

        unique_views: OrderedDict[str, EbaySalesChannelView] = OrderedDict()
        for view in views.iterator():
            tree_id = (view.default_category_tree_id or "").strip()
            if not tree_id:
                continue
            unique_views.setdefault(tree_id, view)

        for view in unique_views.values():
            EbayCategoryNodeSyncFactory(view=view).run()
