from core import models
from sales_channels.models import RemoteCurrency, RemoteVat


class ShopifyCurrency(RemoteCurrency):
    """
    Shopify-specific RemoteCurrency for store presentment currencies.
    """
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the primary currency for this Shopify store."
    )