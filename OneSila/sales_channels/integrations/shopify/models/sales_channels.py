from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.models.sales_channels import SalesChannel, SalesChannelView, RemoteLanguage
import uuid


class ShopifySalesChannel(SalesChannel):
    """
    Shopify-specific Sales Channel model with credentials and config.
    """

    access_token = models.CharField(
        max_length=255,
        help_text="OAuth access token for this Shopify store.",
        null=True, blank=True
    )

    state = models.CharField(
        max_length=64,
        unique=True,
        null=True, blank=True,
        help_text="Unique state used for OAuth verification"
    )

    vendor_property = models.ForeignKey(
        'properties.Property',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The product property that maps to Shopify vendor (brand)."
    )

    class Meta:
        verbose_name = 'Shopify Sales Channel'
        verbose_name_plural = 'Shopify Sales Channels'

    def __str__(self):
        return f"Shopify Store: {self.hostname}"

    def connect(self):
        pass

    def save(self, *args, **kwargs):
        if not self.access_token and not self.state:
            self.state = uuid.uuid4().hex
        super().save(*args, **kwargs)


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