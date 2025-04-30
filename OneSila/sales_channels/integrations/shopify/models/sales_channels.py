from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.models.sales_channels import SalesChannel, SalesChannelView, RemoteLanguage


class ShopifySalesChannel(SalesChannel):
    """
    Shopify-specific Sales Channel model with credentials and config.
    """
    shop_url = models.URLField(max_length=255, help_text="The myshopify.com domain for this store.")
    api_version = models.CharField(
        max_length=32,
        default='2024-07',
        help_text=_('Shopify API version to use for requests.')
    )
    access_token = models.CharField(
        max_length=255,
        help_text="OAuth access token for this Shopify store."
    )

    class Meta:
        verbose_name = 'Shopify Sales Channel'
        verbose_name_plural = 'Shopify Sales Channels'

    def __str__(self):
        return f"Shopify Store: {self.shop_url}"


class ShopifySalesChannelView(SalesChannelView):
    """
    Placeholder for Shopify store views (e.g., theme locales or markets).
    Shopify does not use separate store-views like Magento.
    """
    pass


class ShopifyRemoteLanguage(RemoteLanguage):
    """
    Shopify-specific RemoteLanguage for storefront locales.
    """
    pass