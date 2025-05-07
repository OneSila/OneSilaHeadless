from django.db import models
from sales_channels.models import SalesChannel, RemoteProduct
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


class WoocommerceProduct(RemoteProduct):
    """
    Woocommerce product model
    """
    pass


class WoocommerceAttribute(RemoteProperty):
    """
    Woocommerce attribute model
    """
    pass


class WoocommerceAttributeSelectValue(RemotePropertySelectValue):
    """
    Woocommerce attribute select value model
    """
    pass


class WoocommerceProductProperty(RemoteProductProperty):
    """
    Woocommerce product property model
    """
    pass


class WoocommerceBrand(RemoteObjectMixin, models.Model):
    """
    Woocommerce brand model
    """
    pass
