from sales_channels.models.imports import SalesChannelImport
from core import models


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


class AmazonImportRelationship(models.Model):
    """Store parent-child SKU pairs during async product import."""

    import_process = models.ForeignKey('imports_exports.Import', on_delete=models.CASCADE, related_name='amazon_relationships')
    parent_sku = models.CharField(max_length=255)
    child_sku = models.CharField(max_length=255)

    class Meta:
        unique_together = ("import_process", "parent_sku", "child_sku")
        verbose_name = "Amazon Import Relationship"
        verbose_name_plural = "Amazon Import Relationships"


class AmazonImportBrokenRecord(models.Model):
    """Store parent-child SKU pairs during async product import."""

    import_process = models.ForeignKey('imports_exports.Import', on_delete=models.CASCADE, related_name='amazon_import_broken_records')
    record = models.JSONField(
        blank=True,
        help_text="Store broken record that failed during import."
    )

    class Meta:
        verbose_name = "Amazon Import Broken Record"
        verbose_name_plural = "Amazon Import Broken Records"


class AmazonImportData(models.Model):
    """Stores raw import data for each Amazon product."""

    sales_channel = models.ForeignKey(
        'amazon.AmazonSalesChannel',
        on_delete=models.CASCADE,
        related_name='import_data',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='amazon_import_data',
    )
    view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='import_data',
    )
    data = models.JSONField(blank=True, default=dict)

    class Meta:
        unique_together = ('sales_channel', 'product', 'view')
        verbose_name = 'Amazon Import Data'
        verbose_name_plural = 'Amazon Import Data'
