from sales_channels.models.imports import SalesChannelImport
from django.db import models


class AmazonSalesChannelImport(SalesChannelImport):
    """Amazon-specific import process."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCTS = "products"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCTS, "Products"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Amazon Sales Channel Import"
        verbose_name_plural = "Amazon Sales Channel Imports"
