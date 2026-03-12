from core import models

from sales_channels.models.feeds import SalesChannelFeed


class MiraklSalesChannelFeed(SalesChannelFeed):
    """Mirakl-specific feed batch artifact."""

    STAGE_PRODUCT = "product"
    STAGE_OFFER = "offer"

    STAGE_CHOICES = [
        (STAGE_PRODUCT, "Product"),
        (STAGE_OFFER, "Offer"),
    ]

    stage = models.CharField(max_length=32, choices=STAGE_CHOICES, default=STAGE_PRODUCT)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Sales Channel Feed"
        verbose_name_plural = "Mirakl Sales Channel Feeds"
