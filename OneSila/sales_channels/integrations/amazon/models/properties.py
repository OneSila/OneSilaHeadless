from sales_channels.models.properties import (
    RemoteProperty,
    RemotePropertySelectValue,
    RemoteProductProperty,
)
from core import models
from django.utils.translation import gettext_lazy as _


class AmazonProperty(RemoteProperty):
    """Amazon specific remote property."""

    attribute_code = models.CharField(
        max_length=255,
        help_text="The attribute code used in Amazon for this property.",
        verbose_name="Attribute Code",
    )

    class Meta:
        verbose_name = 'Amazon Property'
        verbose_name_plural = 'Amazon Properties'


class AmazonPropertySelectValue(RemotePropertySelectValue):
    """Amazon specific remote property select value."""
    pass


class AmazonProductProperty(RemoteProductProperty):
    """Amazon specific remote product property."""

    class Meta:
        verbose_name_plural = _('Amazon Product Properties')
