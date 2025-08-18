from core import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from products.models import Product
from sales_channels.models import SalesChannel, SalesChannelView

class AmazonBrowseNode(models.SharedModel):
    remote_id = models.CharField(max_length=50, primary_key=True)  # browseNodeId
    marketplace_id = models.CharField(max_length=20, db_index=True)  # e.g., A1F83G8C2ARO7P

    name = models.CharField(max_length=512, null=True, blank=True)  # browseNodeName
    context_name = models.CharField(max_length=512, null=True, blank=True)  # browseNodeStoreContextName

    has_children = models.BooleanField(default=False)
    is_root = models.BooleanField(default=False, db_index=True)

    child_node_ids = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Only populated if has_children is True"
    )

    browse_path_by_id = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Full browsePathById chain"
    )
    browse_path_by_name = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True,
        help_text="Full browsePathByName chain"
    )

    product_type_definitions = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True
    )

    path_depth = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["marketplace_id"]),
            models.Index(fields=["path_depth"]),
            GinIndex(fields=["product_type_definitions"]),
        ]
        unique_together = ("remote_id", "marketplace_id")

    def __str__(self):
        return f"{self.name} ({self.remote_id})"


class AmazonProductBrowseNode(models.Model):
    """Link a product and view to a recommended browse node."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    sales_channel_view = models.ForeignKey(SalesChannelView, on_delete=models.CASCADE)
    recommended_browse_node_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ("product", "sales_channel_view")

    def __str__(self):
        return f"{self.product} @ {self.sales_channel_view}: {self.recommended_browse_node_id}"
