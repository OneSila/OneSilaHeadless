from sales_channels.models.sales_channels import (
    SalesChannel,
    SalesChannelView,
    RemoteLanguage
)
from sales_channels.exceptions import VariationAlreadyExistsOnWebsite

from core import models
from django.utils.translation import gettext_lazy as _


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
    attribute_set_skeleton_id = models.PositiveIntegerField(
        default=4,
        help_text=_("Default skeleton ID used for attribute set creation during initial import.")
    )
    ean_code_attribute = models.CharField(
        max_length=64,
        default="ean_code",
        help_text=_("Magento attribute code for the EAN code.")
    )

    class Meta:
        verbose_name = 'Magento Sales Channel'
        verbose_name_plural = 'Magento Sales Channels'
        user_exceptions = (VariationAlreadyExistsOnWebsite,)

    def __str__(self):
        return f"Magento Sales Channel: {self.hostname}"

    def connect(self):
        from sales_channels.integrations.magento2.factories.sales_channels.sales_channel import TryConnection

        required_fields = {'hostname', 'host_api_username', 'host_api_key', 'authentication_method'}

        if required_fields.intersection(self.get_dirty_fields().keys()):
            try:
                TryConnection(sales_channel=self)
            except Exception:
                raise Exception(
                    _("Could not connect to the Magento server. Make sure all the details are correctly completed.")
                )


class MagentoSalesChannelView(SalesChannelView):
    """
    Magento-specific Sales Channel View.
    """
    code = models.CharField(max_length=50, help_text="Unique code for the sales channel view.")


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
    store_view_code = models.CharField(max_length=126, help_text="The language code store view (will be used as scope).")
