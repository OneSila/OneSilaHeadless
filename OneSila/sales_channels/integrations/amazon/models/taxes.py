from sales_channels.models import RemoteCurrency, RemoteVat
from core import models


class AmazonCurrency(RemoteCurrency):
    """Amazon remote currency."""
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the primary currency for this Amazon store."
    )


class AmazonVat(RemoteVat):
    """Amazon remote VAT."""
    pass
