from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.models.sales_channels import (
    SalesChannel,
    SalesChannelView,
    RemoteLanguage,
)
import uuid


class AmazonSalesChannel(SalesChannel):
    """Amazon specific Sales Channel."""

    NORTH_AMERICA = "NA"
    EUROPE = "EU"
    FAR_EAST = "FE"

    REGION_CHOICES = (
        (NORTH_AMERICA, _("North America")),
        (EUROPE, _("Europe")),
        (FAR_EAST, _("Far East")),
    )

    COUNTRY_CHOICES = (
        ("CA", "Canada"),
        ("US", "United States"),
        ("MX", "Mexico"),
        ("BR", "Brazil"),

        ("IE", "Ireland"),
        ("ES", "Spain"),
        ("GB", "United Kingdom"),
        ("FR", "France"),
        ("BE", "Belgium"),
        ("NL", "Netherlands"),
        ("DE", "Germany"),
        ("IT", "Italy"),
        ("SE", "Sweden"),
        ("ZA", "South Africa"),
        ("PL", "Poland"),
        ("EG", "Egypt"),
        ("TR", "Turkey"),
        ("SA", "Saudi Arabia"),
        ("AE", "United Arab Emirates"),
        ("IN", "India"),

        ("SG", "Singapore"),
        ("AU", "Australia"),
        ("JP", "Japan"),
    )

    remote_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Selling Partner ID (merchant ID) for Amazon SP-API.",
    )

    refresh_token = models.CharField(
        max_length=512, null=True, blank=True,
        help_text="Refresh token used to generate new access tokens."
    )
    refresh_token_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the refresh token will expire (typically 1 year)."
    )
    access_token = models.CharField(
        max_length=512,
        null=True, blank=True,
        help_text="Access token for API requests."
    )
    expiration_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Expiration datetime of the access token."
    )
    state = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique state used for OAuth verification",
    )
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        null=True,
        blank=True,
        help_text="Country code for Seller Central domain.",
    )

    region = models.CharField(
        max_length=2,
        choices=REGION_CHOICES,
        null=True,
        blank=True,
        help_text="Amazon region of this store."
    )
    connection_error = models.TextField(
        null=True,
        blank=True,
        help_text="Stores the last OAuth connection failure traceback."
    )
    listing_owner = models.BooleanField(
        default=False,
        help_text="Indicates if the sales channel have listing_owner status and can edit or create listings"
    )

    class Meta:
        verbose_name = 'Amazon Sales Channel'
        verbose_name_plural = 'Amazon Sales Channels'

    def __str__(self):
        return f"Amazon Store: {self.hostname}"

    def connect(self):
        pass

    def save(self, *args, **kwargs):
        if not self.access_token and not self.state:
            self.state = uuid.uuid4().hex
        super().save(*args, **kwargs)


class AmazonSalesChannelView(SalesChannelView):
    """Amazon marketplace representation."""
    api_region_code = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    @property
    def language_tag(self) -> str | None:
        """Return the first remote language code for this marketplace."""
        lang = self.remote_languages.first()
        return lang.remote_code if lang else None


class AmazonRemoteLanguage(RemoteLanguage):
    """Amazon remote language linked to a marketplace."""

    sales_channel_view = models.ForeignKey(
        AmazonSalesChannelView,
        on_delete=models.CASCADE,
        related_name='remote_languages',
        null=True,
        blank=True,
        help_text="The marketplace associated with this remote language.",
    )


class AmazonDefaultUnitConfigurator(models.Model):
    """Store default unit configuration for a sales channel attribute."""

    sales_channel = models.ForeignKey(
        SalesChannel,
        on_delete=models.CASCADE,
        related_name="default_unit_configurators",
    )
    marketplace = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        help_text="The Amazon marketplace for this value."
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    selected_unit = models.CharField(max_length=100, null=True, blank=True)
    choices = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("sales_channel", "marketplace", "code")
        verbose_name = "Default Unit Configurator"
        verbose_name_plural = "Default Unit Configurators"
        search_terms = ['name', 'code']

    def __str__(self):
        return f"{self.code} @ {self.sales_channel}"
