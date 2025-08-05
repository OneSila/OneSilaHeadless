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
