from core import models
from sales_channels.models.imports import SalesChannelImport


class MiraklSalesChannelImport(SalesChannelImport):
    """Mirakl import process entry used for schema/product imports only."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCTS = "products"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCTS, "Products"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Mirakl Sales Channel Import"
        verbose_name_plural = "Mirakl Sales Channel Imports"
