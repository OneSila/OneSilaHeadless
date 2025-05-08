from django.db import models
from django.utils.translation import gettext as _
from sales_channels.models import SalesChannel, SalesChannelView, RemoteProduct
from sales_channels.models.properties import RemoteProperty, \
    RemotePropertySelectValue, RemoteProductProperty
from sales_channels.models.mixins import RemoteObjectMixin


class WoocommerceSalesChannel(SalesChannel):
    """
    Woocommerce sales channel model
    """
    API_VERSION_3 = 'wc/v3'
    API_VERSION_CHOICES = [
        (API_VERSION_3, 'Woocommerce API v3'),
    ]

    api_url = models.URLField(help_text="Woocommerce API URL")
    api_key = models.CharField(max_length=255, help_text="Woocommerce API Key")
    api_secret = models.CharField(max_length=255, help_text="Woocommerce API Secret")
    api_version = models.CharField(max_length=5, help_text="Woocommerce API Version",
        choices=API_VERSION_CHOICES)
    timeout = models.IntegerField(default=10, help_text="Woocommerce API Timeout")

    def connect(self):
        from sales_channels.integrations.woocommerce.factories.sales_channels.sales_channel import TryConnection

        required_fields = {'api_url', 'api_key', 'api_secret', 'api_version'}

        if required_fields.intersection(self.get_dirty_fields().keys()):
            try:
                TryConnection(sales_channel=self)
            except Exception:
                raise Exception(
                    _("Could not connect to the Woocommerce server. Make sure all the details are correctly completed.")
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
    pass
