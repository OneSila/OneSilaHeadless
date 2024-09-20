from sales_channels.models.sales_channels import (
    SalesChannel,
    SalesChannelView,
    SalesChannelViewAssign,
    RemoteLanguage
)
from core import models

class MagentoSalesChannel(SalesChannel):
    """
    Magento-specific Sales Channel model with additional fields for authentication and configuration.
    """
    from magento import AuthenticationMethod

    AUTH_METHOD_CHOICES = (
        (AuthenticationMethod.TOKEN.value, 'Token Only'),
        (AuthenticationMethod.PASSWORD.value, 'Username / Password')
    )

    host_api_username = models.CharField(max_length=256, blank=True, null=True)
    host_api_key = models.CharField(max_length=256)
    authentication_method = models.CharField(max_length=3, choices=AUTH_METHOD_CHOICES)

    class Meta:
        verbose_name = 'Magento Sales Channel'
        verbose_name_plural = 'Magento Sales Channels'
        user_exceptions = ()

    def __str__(self):
        return f"Magento Sales Channel: {self.hostname}"


class MagentoSalesChannelView(SalesChannelView):
    """
    Magento-specific Sales Channel View.
    """
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the sales channel view.")


class MagentoRemoteLanguage(RemoteLanguage):
    """
    Magento-specific Remote Language.
    """
    sales_channel_view = models.ForeignKey(
        MagentoSalesChannelView,
        on_delete=models.CASCADE,
        related_name='remote_languages',
        help_text="The sales channel view associated with this remote language."
    )
