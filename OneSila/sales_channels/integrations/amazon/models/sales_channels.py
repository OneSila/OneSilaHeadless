from django.utils.translation import gettext_lazy as _
from core import models
from sales_channels.models.sales_channels import SalesChannel, SalesChannelView, RemoteLanguage


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

    refresh_token = models.CharField(
        max_length=512,
        help_text="Refresh token used to generate new access tokens."
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
    region = models.CharField(
        max_length=2,
        choices=REGION_CHOICES,
        null=True,
        blank=True,
        help_text="Amazon region of this store."
    )

    class Meta:
        verbose_name = 'Amazon Sales Channel'
        verbose_name_plural = 'Amazon Sales Channels'

    def __str__(self):
        return f"Amazon Store: {self.hostname}"

    def connect(self):
        pass


class AmazonSalesChannelView(SalesChannelView):
    """Amazon marketplace representation."""



class AmazonRemoteLanguage(RemoteLanguage):
    """Amazon remote language placeholder."""

    pass
