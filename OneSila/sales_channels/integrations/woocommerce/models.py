from core import models
from django.utils.translation import gettext as _
from sales_channels.models import SalesChannel, SalesChannelView, \
    RemoteProduct, RemoteEanCode, RemoteCurrency, RemoteLanguage, \
    RemotePrice, RemoteProductContent
from sales_channels.models.properties import RemoteProperty, \
    RemotePropertySelectValue, RemoteProductProperty
from sales_channels.models.products import RemoteImageProductAssociation
from django.utils.translation import gettext_lazy as _
from sales_channels.exceptions import (
    ConfiguratorPropertyNotFilterable,
    VariationAlreadyExistsOnWebsite,
)


class WoocommerceSalesChannel(SalesChannel):
    """
    Woocommerce sales channel model
    """
    API_VERSION_3 = 'wc/v3'
    API_VERSION_CHOICES = [
        (API_VERSION_3, 'Woocommerce API v3'),
    ]

    api_key = models.CharField(max_length=255, help_text="Woocommerce API Key")
    api_secret = models.CharField(max_length=255, help_text="Woocommerce API Secret")
    api_version = models.CharField(max_length=5, help_text="Woocommerce API Version",
        choices=API_VERSION_CHOICES, default=API_VERSION_3)
    timeout = models.IntegerField(default=10, help_text="Woocommerce API Timeout")

    def connect(self):
        from sales_channels.integrations.woocommerce.factories.sales_channels import TryConnection

        required_fields = {'hostname', 'api_key', 'api_secret', 'api_version'}

        if required_fields.intersection(self.get_dirty_fields().keys()):
            try:
                conn = TryConnection(sales_channel=self)
                conn.try_connection()
            except Exception:
                raise Exception(
                    _("Could not connect to the Woocommerce server. Make sure all the details are correctly completed.")
                )

    class Meta:
        user_exceptions = (
            VariationAlreadyExistsOnWebsite,
            ConfiguratorPropertyNotFilterable,
        )


class WoocommerceSalesChannelView(SalesChannelView):
    """
    Woocommerce-specific Sales Channel View.
    """
    pass
    # code = models.CharField(max_length=50, help_text="Unique code for the sales channel view.")


class WoocommerceGlobalAttribute(RemoteProperty):
    """
    Woocommerce attribute model
    """
    class Meta:
        verbose_name_plural = _('Woocommerce Product Properties')


class WoocommerceGlobalAttributeValue(RemotePropertySelectValue):
    """
    Woocommerce attribute value model for global attributes
    """
    pass


class WoocommerceProduct(RemoteProduct):
    """
    Woocommerce product model
    """
    pass


class WoocommerceProductProperty(RemoteProductProperty):
    """
    Woocommerce product property model
    """
    pass


class WoocommerceEanCode(RemoteEanCode):
    """
    Woocommerce ean code model
    """
    pass


class WoocommerceMediaThroughProduct(RemoteImageProductAssociation):
    """
    Woocommerce media through product model
    """
    pass


class WoocommerceCurrency(RemoteCurrency):
    """
    Woocommerce currency model
    """
    class Meta:
        verbose_name_plural = _('Woocommerce Currencies')


class WoocommerceRemoteLanguage(RemoteLanguage):
    """
    Woocommerce remote language model
    """
    pass


class WoocommercePrice(RemotePrice):
    """
    Woocommerce price model
    """
    pass


class WoocommerceProductContent(RemoteProductContent):
    """
    Woocommerce product content model
    """
    pass
