from __future__ import annotations

from urllib.parse import urlparse

from django.utils.translation import gettext_lazy as _

from core import models
from sales_channels.integrations.mirakl.sub_type_constants import (
    DEFAULT_MIRAKL_SUB_TYPE,
    MIRAKL_SUB_TYPE_CHOICES,
    infer_mirakl_sub_type_from_hostname,
)
from sales_channels.exceptions import (
    InspectorMissingInformationError,
    MiraklPayloadValidationError,
    MissingMappingError,
    PreFlightCheckError,
    RemotePropertyValueNotMapped,
    SkipSyncBecauseOfStatusException,
    VariationAlreadyExistsOnWebsite,
)
from sales_channels.models.sales_channels import RemoteLanguage, SalesChannel, SalesChannelView
from sales_channels.models.taxes import RemoteCurrency


class MiraklSalesChannel(SalesChannel):
    """Mirakl sales channel scoped to one Mirakl shop."""

    CSV_DELIMITER_COMMA = "COMMA"
    CSV_DELIMITER_SEMICOLON = "SEMICOLON"
    CSV_DELIMITER_CHOICES = [
        (CSV_DELIMITER_COMMA, "Comma"),
        (CSV_DELIMITER_SEMICOLON, "Semicolon"),
    ]

    sub_type = models.CharField(
        max_length=128,
        choices=MIRAKL_SUB_TYPE_CHOICES,
        default=DEFAULT_MIRAKL_SUB_TYPE,
        help_text="Known Mirakl operator subtype for frontend and integration-specific behavior.",
    )
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
    product_import_only_on_leaf = models.BooleanField(
        default=False,
        help_text="Prevents the import of products into non-leaf categories when enabled by the operator.",
    )
    list_of_multiple_values_separator = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Separator used by the operator for multiple-values list fields.",
    )
    offer_prices_decimals = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of decimals allowed in offer prices.",
    )
    operator_csv_delimiter = models.CharField(
        max_length=16,
        blank=True,
        default="",
        choices=CSV_DELIMITER_CHOICES,
        help_text="Delimiter expected in operator CSV files.",
    )
    last_differential_issues_fetch = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful Mirakl differential issues fetch boundary.",
    )
    last_full_issues_fetch = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful Mirakl full issues fetch boundary.",
    )
    last_product_imports_request_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful Mirakl P51 product imports polling boundary.",
    )

    class Meta:
        verbose_name = "Mirakl Sales Channel"
        verbose_name_plural = "Mirakl Sales Channels"
        user_exceptions = (
            InspectorMissingInformationError,
            MiraklPayloadValidationError,
            MissingMappingError,
            PreFlightCheckError,
            RemotePropertyValueNotMapped,
            SkipSyncBecauseOfStatusException,
            VariationAlreadyExistsOnWebsite,
        )

    def __str__(self) -> str:
        return f"Mirakl Store: {self.hostname}"

    def save(self, *args, **kwargs):
        if self.sub_type == DEFAULT_MIRAKL_SUB_TYPE and self.hostname:
            inferred_sub_type = infer_mirakl_sub_type_from_hostname(hostname=self.hostname)
            if inferred_sub_type != DEFAULT_MIRAKL_SUB_TYPE:
                self.sub_type = inferred_sub_type
        super().save(*args, **kwargs)

    @property
    def connected(self) -> bool:
        return bool(self.hostname and self.shop_id and self.api_key)

    def connect(self) -> bool:
        if not self.connected:
            return False

        required_fields = {"hostname", "shop_id", "api_key"}
        if required_fields.intersection(self.get_dirty_fields().keys()):
            from sales_channels.integrations.mirakl.factories.sales_channels import ValidateMiraklCredentialsFactory

            try:
                factory = ValidateMiraklCredentialsFactory(sales_channel=self)
                account_info = factory.validate_credentials()
                platform_configuration = factory.get_platform_configuration()
                self.raw_data = account_info or {}
                factory.apply_platform_configuration(
                    instance=self,
                    platform_configuration=platform_configuration,
                )

            except Exception as exc:
                raise Exception(
                    _("Could not connect to Mirakl. Make sure the hostname, shop ID, and API key are correct.")
                ) from exc

        return True

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

    @property
    def csv_delimiter(self) -> str:
        if self.operator_csv_delimiter == self.CSV_DELIMITER_SEMICOLON:
            return ";"
        return ","


class MiraklSalesChannelView(SalesChannelView):
    """Mirakl channel exposed under a seller shop."""

    description = models.TextField(
        null=True,
        blank=True,
        help_text="Mirakl channel description.",
    )

    class Meta:
        verbose_name = "Mirakl Sales Channel View"
        verbose_name_plural = "Mirakl Sales Channel Views"

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

    class Meta:
        verbose_name = "Mirakl Remote Language"
        verbose_name_plural = "Mirakl Remote Languages"

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

    class Meta:
        verbose_name = "Mirakl Remote Currency"
        verbose_name_plural = _("Mirakl Remote Currencies")

    def __str__(self) -> str:
        return self.remote_code or super().__str__()
