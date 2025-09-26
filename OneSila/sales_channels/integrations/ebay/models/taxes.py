from sales_channels.models.taxes import RemoteCurrency
from django.db import models
from django.utils.translation import gettext_lazy as _


class EbayCurrency(RemoteCurrency):
    """eBay currency model."""

    sales_channel_view = models.ForeignKey(
        'ebay.EbaySalesChannelView',
        on_delete=models.CASCADE,
        related_name='remote_currencies',
        null=True,
        blank=True,
        help_text="The marketplace associated with this remote currency.",
    )

    class Meta:
        verbose_name_plural = _("eBay Currencies")

