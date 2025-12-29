"""Sales channel models for the Shein integration."""

import uuid
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core import models

from sales_channels.exceptions import PreFlightCheckError, SkipSyncBecauseOfStatusException
from sales_channels.integrations.shein.exceptions import SheinPreValidationError, SheinResponseException
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.sales_channels import (
    RemoteLanguage,
    SalesChannel,
    SalesChannelView,
)
from sales_channels.models.taxes import RemoteCurrency


class SheinSalesChannel(SalesChannel):
    """Minimal Shein sales channel footprint until OAuth is implemented."""

    remote_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Remote Shein identifier for the connected store.",
    )

    state = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Opaque value used to validate the OAuth redirect flow.",
    )

    open_key_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Shein openKeyId returned by the authorization token exchange.",
    )

    secret_key_encrypted = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Encrypted secretKey received from Shein (base64 encoded).",
    )

    secret_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Decrypted secret key used to sign Shein API requests.",
    )

    supplier_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Supplier identifier returned by Shein during OAuth validation.",
    )

    supplier_source = models.IntegerField(
        null=True,
        blank=True,
        help_text="Supplier source value provided in the authorization payload.",
    )

    supplier_business_mode = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Supplier business mode reported by Shein.",
    )

    last_authorized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful Shein authorization.",
    )

    class Meta:
        verbose_name = "Shein Sales Channel"
        verbose_name_plural = "Shein Sales Channels"
        user_exceptions = (
            SheinResponseException,
            SheinPreValidationError,
            PreFlightCheckError,
            SkipSyncBecauseOfStatusException,
        )

    def __str__(self) -> str:
        return f"Shein Store: {self.hostname}"

    def connect(self) -> bool:
        """Report whether OAuth credentials (secret key) are available."""

        return bool(self.secret_key)

    def save(self, *args, **kwargs):
        if not self.state:
            self.state = uuid.uuid4().hex
        super().save(*args, **kwargs)


class SheinSalesChannelView(SalesChannelView):
    """Representation of a Shein storefront / sub-site."""

    site_status = models.IntegerField(
        null=True,
        blank=True,
        help_text="Raw site status integer reported by Shein.",
    )
    store_type = models.IntegerField(
        null=True,
        blank=True,
        help_text="Store type reported by Shein.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the default storefront for this Shein sales channel.",
    )
    merchant_location_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Selected warehouse code for this storefront.",
    )
    merchant_location_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="Available warehouse codes returned by Shein.",
    )

    class Meta:
        verbose_name = "Shein Sales Channel View"
        verbose_name_plural = "Shein Sales Channel Views"

    def clean(self):
        super().clean()
        if self.is_default:
            exists = (
                SheinSalesChannelView.objects.filter(
                    sales_channel=self.sales_channel,
                    is_default=True,
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if exists:
                raise ValidationError(
                    _("You can only have one default Shein storefront per channel."),
                )

    def __str__(self) -> str:
        return self.name or super().__str__()

    @property
    def is_active(self) -> Optional[bool]:
        """Return True when the remote site status flags the view as available."""

        if self.site_status is None:
            return None
        return self.site_status == 1


class SheinRemoteCurrency(RemoteCurrency):
    """Remote currency information advertised by Shein."""

    sales_channel_view = models.ForeignKey(
        "shein.SheinSalesChannelView",
        on_delete=models.SET_NULL,
        related_name="remote_currencies",
        null=True,
        blank=True,
        help_text="Storefront/sub-site associated with this currency, if known.",
    )
    symbol_left = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text="Currency symbol placed to the left of the value.",
    )
    symbol_right = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text="Currency symbol placed to the right of the value.",
    )

    class Meta:
        verbose_name = "Shein Remote Currency"
        verbose_name_plural = "Shein Remote Currencies"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel_view"],
                condition=models.Q(sales_channel_view__isnull=False),
                name="unique_shein_currency_per_view",
            )
        ]


class SheinRemoteLanguage(RemoteLanguage):
    """Remote language metadata exposed for a Shein storefront."""

    remote_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Display name for the remote language.",
    )
    sales_channel_view = models.ForeignKey(
        SheinSalesChannelView,
        on_delete=models.SET_NULL,
        related_name='remote_languages',
        null=True,
        blank=True,
        help_text="Storefront associated with this language, if known.",
    )
