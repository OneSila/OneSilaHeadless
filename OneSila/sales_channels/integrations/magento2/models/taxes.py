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
    is_default = models.BooleanField(
        default=False,
        help_text="Indicates whether this is the default/global currency for Magento price updates (no scope)."
    )

    store_view_codes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of store view codes related to this website/currency."
    )


class MagentoTaxClass(RemoteVat):
    """
    Magento-specific model for remote vat rate.
    """
    pass
