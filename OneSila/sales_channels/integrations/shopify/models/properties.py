from sales_channels.models.properties import RemoteProductProperty
from core import models

class ShopifyProductProperty(RemoteProductProperty):
    """
    Shopify-specific model linking a product to a metafield value.
    Shopify does not manage standalone property definitions or select values.
    This are the individual metafield assigned to product
    """

    # override remote property to allow null
    remote_property = models.ForeignKey(
        'sales_channels.RemoteProperty',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Not used for Shopify—Shopify has no separate property definitions."
    )