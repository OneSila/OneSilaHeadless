from core import models
from sales_channels.models.imports import SalesChannelImport


class MiraklSalesChannelImport(SalesChannelImport):
    """Mirakl async import tracking."""

    TYPE_SCHEMA = "schema"
    TYPE_PRODUCT = "product"
    TYPE_OFFER = "offer"
    TYPE_PRICING = "pricing"

    TYPE_CHOICES = [
        (TYPE_SCHEMA, "Schema"),
        (TYPE_PRODUCT, "Product"),
        (TYPE_OFFER, "Offer"),
        (TYPE_PRICING, "Pricing"),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    remote_import_id = models.CharField(max_length=255, blank=True, default="")
    source_file_name = models.CharField(max_length=255, blank=True, default="")
    has_error_report = models.BooleanField(default=False)
    has_transformed_file = models.BooleanField(default=False)
    summary_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Sales Channel Import"
        verbose_name_plural = "Mirakl Sales Channel Imports"
