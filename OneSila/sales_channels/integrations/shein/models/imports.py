"""Shein-specific import models."""

from core import models
from sales_channels.models.imports import SalesChannelImport


class SheinSalesChannelImport(SalesChannelImport):
    """Import process tailored for the Shein integration."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCTS = "products"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCTS, "Products"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Shein Sales Channel Import"
        verbose_name_plural = "Shein Sales Channel Imports"
