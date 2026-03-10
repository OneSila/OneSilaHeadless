from __future__ import annotations

from urllib.parse import urlparse

from django.utils.translation import gettext_lazy as _

from core import models
from sales_channels.models.sales_channels import RemoteLanguage, SalesChannel, SalesChannelView
from sales_channels.models.taxes import RemoteCurrency


class MiraklSalesChannel(SalesChannel):
    """Mirakl sales channel scoped to one Mirakl shop."""

    shop_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Mirakl shop identifier used to scope API requests.",
    )
    api_key = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="Mirakl API key sent in the Authorization header.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached shop/account metadata returned by Mirakl.",
    )

    class Meta:
        verbose_name = "Mirakl Sales Channel"
        verbose_name_plural = "Mirakl Sales Channels"
        constraints = [
            models.UniqueConstraint(
                fields=["multi_tenant_company", "hostname", "shop_id"],
                name="unique_mirakl_shop_per_company",
            ),
        ]

    def __str__(self) -> str:
        return f"Mirakl Store: {self.hostname}"

    def connect(self) -> bool:
        return bool(self.hostname and self.shop_id and self.api_key)

    @property
    def normalized_base_url(self) -> str:
        hostname = str(self.hostname or "").strip()
        if not hostname:
            return ""
        if "://" not in hostname:
            hostname = f"https://{hostname}"
        parsed = urlparse(hostname)
        if not parsed.scheme or not parsed.netloc:
            return hostname.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


class MiraklSalesChannelView(SalesChannelView):
    """Mirakl channel exposed under a seller shop."""

    description = models.TextField(
        null=True,
        blank=True,
        help_text="Mirakl channel description.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original Mirakl channel payload.",
    )

    class Meta:
        verbose_name = "Mirakl Sales Channel View"
        verbose_name_plural = "Mirakl Sales Channel Views"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_id"],
                name="unique_mirakl_view_per_channel",
            ),
        ]

    def __str__(self) -> str:
        return self.name or self.remote_id or super().__str__()


class MiraklRemoteLanguage(RemoteLanguage):
    """Mirakl locale metadata."""

    label = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Display label returned by Mirakl for the locale.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the default locale when known.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original Mirakl locale payload.",
    )

    class Meta:
        verbose_name = "Mirakl Remote Language"
        verbose_name_plural = "Mirakl Remote Languages"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_code"],
                name="unique_mirakl_language_per_channel",
            ),
        ]

    def __str__(self) -> str:
        return self.label or self.remote_code or super().__str__()


class MiraklRemoteCurrency(RemoteCurrency):
    """Mirakl currency metadata."""

    label = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Display label returned by Mirakl for the currency.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Marks the default currency for the Mirakl shop.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original Mirakl currency payload.",
    )

    class Meta:
        verbose_name = "Mirakl Remote Currency"
        verbose_name_plural = _("Mirakl Remote Currencies")
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_code"],
                name="unique_mirakl_currency_per_channel",
            ),
        ]

    def __str__(self) -> str:
        return self.remote_code or super().__str__()
