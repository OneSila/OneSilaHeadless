from core import models
from sales_channels.models import RemoteCurrency, RemoteVat


class ShopifyCurrency(RemoteCurrency):
    """
    Shopify-specific RemoteCurrency for store presentment currencies.
    """
    currency_code = models.CharField(
        max_length=10,
        help_text="ISO code for the currency (e.g., 'USD', 'EUR')."
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the primary currency for this Shopify store."
    )