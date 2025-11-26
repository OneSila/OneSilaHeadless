"""eBay-specific import models."""

from django.db import models

from sales_channels.models.imports import SalesChannelImport


class EbaySalesChannelImport(SalesChannelImport):
    """Import process tailored for the eBay integration."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCTS = "products"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCTS, "Products"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    content_class = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        verbose_name = "eBay Sales Channel Import"
        verbose_name_plural = "eBay Sales Channel Imports"
