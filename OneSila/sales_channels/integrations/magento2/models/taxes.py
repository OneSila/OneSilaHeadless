from sales_channels.integrations.magento2.models import MagentoSalesChannelView
from sales_channels.models import RemoteCurrency
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