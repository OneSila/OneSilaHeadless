from sales_channels.integrations.magento2.models import MagentoSalesChannelView
from sales_channels.models import RemoteCurrency, RemoteVat
from core import models

class MagentoCurrency(RemoteCurrency):
    """
    Magento-specific Remote Currency.
    """
    sales_channel_view = models.ForeignKey(
        MagentoSalesChannelView,
        on_delete=models.CASCADE,
        related_name='remote_currencies',
        help_text="The sales channel view associated with this remote currency."
    )
    store_view_code = models.CharField(max_length=126, help_text="The language code store view (will be used as scope).")


class MagentoTaxClass(RemoteVat):
    """
    Magento-specific model for remote vat rate.
    """
    pass