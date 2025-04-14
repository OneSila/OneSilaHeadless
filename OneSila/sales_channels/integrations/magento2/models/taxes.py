from sales_channels.integrations.magento2.models import MagentoSalesChannelView
from sales_channels.models import RemoteCurrency, RemoteVat
from core import models

class MagentoCurrency(RemoteCurrency):
    """
    Magento-specific Remote Currency.
    """
    website_code = models.CharField(
        max_length=64,
        help_text="Magento website code. Prices are scoped at the website level."
    )


class MagentoTaxClass(RemoteVat):
    """
    Magento-specific model for remote vat rate.
    """
    pass