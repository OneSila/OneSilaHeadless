from core import models
from core.managers import Manager
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from products.models import Product
from sales_channels.models import SalesChannel, SalesChannelView
from sales_channels.models.products import RemoteProductCategory

class AmazonBrowseNode(models.SharedModel):
    remote_id = models.CharField(max_length=50, db_index=True)  # browseNodeId
    marketplace_id = models.CharField(max_length=20, db_index=True)  # e.g., A1F83G8C2ARO7P

    name = models.CharField(max_length=512, null=True, blank=True)  # browseNodeName
    context_name = models.CharField(max_length=512, null=True, blank=True)  # browseNodeStoreContextName

    has_children = models.BooleanField(default=False)
    is_root = models.BooleanField(default=False, db_index=True)

    parent_node = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_nodes",
    )

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
    objects = Manager()

    class Meta:
        indexes = [
            models.Index(fields=["marketplace_id"]),
            models.Index(fields=["path_depth"]),
            GinIndex(fields=["product_type_definitions"]),
        ]
        unique_together = ("remote_id", "marketplace_id")
        search_terms = ["remote_id", "name", "context_name", "marketplace_id"]

    def __str__(self):
        return f"{self.name} ({self.remote_id})"


class AmazonProductBrowseNodeOld(models.Model):
    """Link a product and view to a recommended browse node."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    view = models.ForeignKey(SalesChannelView, on_delete=models.CASCADE)
    recommended_browse_node_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ("product", "view")

    def __str__(self):
        return f"{self.product} @ {self.view}: {self.recommended_browse_node_id}"


class AmazonProductBrowseNode(RemoteProductCategory):

    class Meta:
        verbose_name = "Amazon Product Browse Node"
        verbose_name_plural = "Amazon Product Browse Nodes"

    def __str__(self):
        return f"{self.product} @ {self.view}: {self.remote_id}"

    # @TODO: Come back at this later right now this break 80+ tests
    # this was not initially here
    # def clean(self):
    #     super().clean()
    #
    #     remote_id = (self.remote_id or "").strip()
    #     if not remote_id:
    #         return
    #
    #     categories = AmazonBrowseNode.objects.filter(remote_id=remote_id)
    #
    #     marketplace_id = None
    #     if self.view_id:
    #         if hasattr(self, "view") and self.view is not None:
    #             marketplace_id = self.view.remote_id
    #         else:
    #             marketplace_id = SalesChannelView.objects.filter(
    #                 id=self.view_id
    #             ).values_list("remote_id", flat=True).first()
    #
    #     if marketplace_id:
    #         categories = categories.filter(marketplace_id=marketplace_id)
    #
    #     try:
    #         category = categories.get()
    #     except AmazonBrowseNode.DoesNotExist as exc:
    #         raise ValidationError(
    #             {"remote_id": "Amazon browse node does not exist for the given remote ID."}
    #         ) from exc
    #     except AmazonBrowseNode.MultipleObjectsReturned as exc:
    #         raise ValidationError(
    #             {"remote_id": "Multiple Amazon browse nodes found for the given remote ID."}
    #         ) from exc
    #
    #     if category.has_children:
    #         raise ValidationError({"remote_id": "Only leaf Amazon browse nodes can be assigned."})
    #
    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     return super().save(*args, **kwargs)
