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
    tracking_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        hostname = getattr(self.sales_channel, "hostname", "") or "Mirakl"
        import_type = self.get_type_display() if self.type else "Import"
        percentage = getattr(self, "percentage", 0) or 0
        return f"{hostname} | {import_type} | {percentage}%"

    class Meta:
        verbose_name = "Mirakl Sales Channel Import"
        verbose_name_plural = "Mirakl Sales Channel Imports"
