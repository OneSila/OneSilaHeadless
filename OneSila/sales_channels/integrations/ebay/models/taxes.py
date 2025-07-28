from sales_channels.models.taxes import RemoteCurrency
from django.utils.translation import gettext_lazy as _


class EbayCurrency(RemoteCurrency):
    """eBay currency model."""

    class Meta:
        verbose_name_plural = _("eBay Currencies")
