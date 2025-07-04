from sales_channels.models import RemoteCurrency, RemoteVat
from core import models


class AmazonCurrency(RemoteCurrency):
    """Amazon remote currency linked to a marketplace."""

    sales_channel_view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='remote_currencies',
        null=True,
        blank=True,
        help_text="The marketplace associated with this remote currency.",
    )

class AmazonTaxCode(RemoteVat):
    """Amazon remote VAT."""
    pass
