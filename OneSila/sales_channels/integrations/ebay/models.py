from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.models.sales_channels import SalesChannel, SalesChannelView, RemoteLanguage
from sales_channels.models.products import (
    RemoteProduct, RemoteInventory, RemotePrice, RemoteProductContent,
    RemoteImageProductAssociation, RemoteCategory, RemoteEanCode,
)
from sales_channels.models.properties import (
    RemoteProperty, RemotePropertySelectValue, RemoteProductProperty,
)
from sales_channels.models.orders import RemoteOrder, RemoteOrderItem
from sales_channels.models.taxes import RemoteCurrency
import uuid


class EbaySalesChannel(SalesChannel):
    """eBay specific Sales Channel."""

    PRODUCTION = "production"
    SANDBOX = "sandbox"

    ENV_CHOICES = (
        (PRODUCTION, _("Production")),
        (SANDBOX, _("Sandbox")),
    )

    environment = models.CharField(
        max_length=16,
        choices=ENV_CHOICES,
        default=PRODUCTION,
        help_text="eBay environment to use",
    )
    remote_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="User ID for the eBay account.",
    )
    refresh_token = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Refresh token used to generate new access tokens.",
    )
    refresh_token_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the refresh token will expire.",
    )
    access_token = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Access token for API requests.",
    )
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expiration datetime of the access token.",
    )
    state = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique state used for OAuth verification",
    )
    connection_error = models.TextField(
        null=True,
        blank=True,
        help_text="Stores the last OAuth connection failure traceback.",
    )

    class Meta:
        verbose_name = "eBay Sales Channel"
        verbose_name_plural = "eBay Sales Channels"

    def __str__(self):
        return f"eBay Store: {self.hostname}"

    def connect(self):
        pass

    def save(self, *args, **kwargs):
        if not self.access_token and not self.state:
            self.state = uuid.uuid4().hex
        super().save(*args, **kwargs)


class EbaySalesChannelView(SalesChannelView):
    """eBay marketplace or site representation."""
    pass


class EbayRemoteLanguage(RemoteLanguage):
    """eBay remote language model."""
    pass


class EbayProperty(RemoteProperty):
    """eBay attribute model."""
    pass


class EbayPropertySelectValue(RemotePropertySelectValue):
    """eBay attribute value model."""
    pass


class EbayProduct(RemoteProduct):
    """eBay product model."""
    pass


class EbayProductProperty(RemoteProductProperty):
    """eBay product property model."""
    pass


class EbayEanCode(RemoteEanCode):
    """eBay EAN code model."""
    pass


class EbayMediaThroughProduct(RemoteImageProductAssociation):
    """eBay media through product model."""
    pass


class EbayCurrency(RemoteCurrency):
    """eBay currency model."""

    class Meta:
        verbose_name_plural = _("eBay Currencies")


class EbayPrice(RemotePrice):
    """eBay price model."""
    pass


class EbayProductContent(RemoteProductContent):
    """eBay product content model."""
    pass


class EbayOrder(RemoteOrder):
    """eBay order model."""
    pass


class EbayOrderItem(RemoteOrderItem):
    """eBay order item model."""
    pass


