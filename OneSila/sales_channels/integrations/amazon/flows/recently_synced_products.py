from datetime import timedelta
from django.utils import timezone
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonSalesChannelView
from sales_channels.integrations.amazon.factories.sales_channels.recently_synced_products import (
    FetchRecentlySyncedProductFactory,
)


def refresh_recent_amazon_products_flow():
    """Refresh data for Amazon products synced in the last 15 minutes."""
    cutoff = timezone.now() - timedelta(minutes=15)
    products = AmazonProduct.objects.filter(last_sync_at__gte=cutoff)
    for product in products.iterator():
        marketplaces = product.created_marketplaces or []
        views = AmazonSalesChannelView.objects.filter(
            sales_channel=product.sales_channel, remote_id__in=marketplaces
        )
        for view in views:
            fac = FetchRecentlySyncedProductFactory(
                remote_product=product, view=view, match_images=True
            )
            fac.run()
