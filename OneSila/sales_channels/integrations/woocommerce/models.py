# Create all of your mirror-models in the model structure.
# Keep it clean, and split out files if you need to.
# This will depend on the structure of the remote locaion.

from django.db import models
from sales_channels.models import SalesChannel, RemoteProduct


class WoocommerceSalesChannel(SalesChannel):
    """
    Woocommerce sales channel model
    Add Woocommerce-specific fields here
    """
    api_url = models.URLField(help_text="Woocommerce API URL")
    api_key = models.CharField(max_length=255, help_text="Woocommerce API Key")
    api_secret = models.CharField(max_length=255, help_text="Woocommerce API Secret")

    class Meta:
        verbose_name = "Woocommerce Sales Channel"
        verbose_name_plural = "Woocommerce Sales Channels"


class WoocommerceProduct(RemoteProduct):
    """
    Woocommerce product model
    Add Woocommerce-specific fields here
    """
    remote_id = models.CharField(max_length=255, help_text="Woocommerce product ID")

    class Meta:
        verbose_name = "Woocommerce Product"
        verbose_name_plural = "Woocommerce Products"
