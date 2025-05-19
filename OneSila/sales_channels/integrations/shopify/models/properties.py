from sales_channels.integrations.shopify.constants import DEFAULT_METAFIELD_NAMESPACE
from sales_channels.models.properties import RemoteProductProperty
from core import models

class ShopifyProductProperty(RemoteProductProperty):
    """
    Shopify-specific model linking a product to a metafield value.
    Shopify does not manage standalone property definitions or select values.
    This are the individual metafield assigned to product
    """
    key = models.CharField(max_length=256)
    namespace = models.CharField(max_length=64, default=DEFAULT_METAFIELD_NAMESPACE)