from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.integrations.ebay.constants import  WEIGHT_UNIT_CHOICES, LENGTH_UNIT_CHOICES
from sales_channels.integrations.ebay.exceptions import EbayResponseException
from sales_channels.models.sales_channels import SalesChannel, SalesChannelView, RemoteLanguage
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
        max_length=2048,
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
        max_length=4096,
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
        user_exceptions = (EbayResponseException,)

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
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the default marketplace for this eBay store.",
    )

    # --- Policies ---
    fulfillment_policy_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Selected Fulfillment Policy ID",
    )
    fulfillment_policy_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of fulfillment policies (as returned from eBay API).",
    )

    payment_policy_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Selected Payment Policy ID",
    )
    payment_policy_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of payment policies.",
    )

    return_policy_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Selected Return Policy ID",
    )
    return_policy_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of return policies.",
    )

    # --- Inventory Location ---
    merchant_location_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Selected inventory location key.",
    )
    merchant_location_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available inventory locations.",
    )

    # --- Package Measurements ---
    length_unit = models.CharField(
        max_length=16,
        choices=LENGTH_UNIT_CHOICES,
        null=True,
        blank=True,
        help_text="Unit of measure for package dimensions.",
    )

    weight_unit = models.CharField(
        max_length=16,
        choices=WEIGHT_UNIT_CHOICES,
        null=True,
        blank=True,
        help_text="Unit of measure for package weight.",
    )

    # --- Category Tree ---
    default_category_tree_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Default category tree ID for this marketplace.",
    )


class EbayRemoteLanguage(RemoteLanguage):
    """eBay remote language model."""
    sales_channel_view = models.ForeignKey(
        EbaySalesChannelView,
        on_delete=models.CASCADE,
        related_name='remote_languages',
        null=True,
        blank=True,
        help_text="The marketplace associated with this remote language.",
    )
