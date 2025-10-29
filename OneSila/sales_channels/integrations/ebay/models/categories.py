from django.core.exceptions import ValidationError

from core import models
from products.models import Product
from sales_channels.integrations.ebay.managers import EbayCategoryManager
from sales_channels.models import SalesChannel, SalesChannelView


class EbayCategory(models.SharedModel):
    marketplace_default_tree_id = models.CharField(max_length=50, db_index=True)
    remote_id = models.CharField(max_length=50)
    name = models.CharField(max_length=512)
    full_name = models.CharField(max_length=512)
    has_children = models.BooleanField(default=False)
    is_root = models.BooleanField(default=False, db_index=True)
    parent_node = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_nodes",
    )

    objects = EbayCategoryManager()

    class Meta:
        unique_together = ("marketplace_default_tree_id", "remote_id")
        ordering = ("marketplace_default_tree_id", "full_name")
        search_terms = ['remote_id', 'name', 'full_name']

    def __str__(self) -> str:
        display_name = self.full_name or self.name
        return f"{display_name} ({self.remote_id})"


class EbayProductCategory(models.Model):
    """Link a product and view to a recommended eBay category."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    view = models.ForeignKey(SalesChannelView, on_delete=models.CASCADE)
    remote_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ("product", "view")

    def __str__(self) -> str:
        return f"{self.product} @ {self.view}: {self.remote_id}"

    def clean(self):
        super().clean()

        remote_id = (self.remote_id or "").strip()
        if not remote_id:
            return

        tree_id = getattr(self.view, "default_category_tree_id", None)
        categories = EbayCategory.objects.filter(remote_id=remote_id)
        if tree_id:
            categories = categories.filter(marketplace_default_tree_id=tree_id)

        try:
            category = categories.get()
        except EbayCategory.DoesNotExist as exc:
            raise ValidationError({"remote_id": "eBay category does not exist for the given remote ID."}) from exc
        except EbayCategory.MultipleObjectsReturned as exc:
            raise ValidationError({"remote_id": "Multiple eBay categories found for the given remote ID."}) from exc

        if category.has_children:
            raise ValidationError({"remote_id": "Only leaf eBay categories can be assigned."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
