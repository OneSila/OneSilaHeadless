from django.core.exceptions import ValidationError

from core import models
from products.models import Product
from sales_channels.integrations.ebay.managers import EbayCategoryManager
from sales_channels.models import SalesChannel, SalesChannelView
from sales_channels.models.products import RemoteProductCategory


class EbayCategory(models.SharedModel):
    marketplace_default_tree_id = models.CharField(max_length=50, db_index=True)
    remote_id = models.CharField(max_length=50)
    name = models.CharField(max_length=512)
    full_name = models.CharField(max_length=512)
    has_children = models.BooleanField(default=False)
    is_root = models.BooleanField(default=False, db_index=True)
    configurator_properties = models.JSONField(default=list, blank=True)
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


class EbayProductCategoryOld(models.Model):
    """Link a product and view to a recommended eBay category."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    view = models.ForeignKey(SalesChannelView, on_delete=models.CASCADE)
    remote_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ("product", "view")
        indexes = [
            models.Index(fields=["product", "view"]),
        ]



class EbayProductCategory(RemoteProductCategory):
    secondary_category_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "eBay Product Category"
        verbose_name_plural = "eBay Product Categories"

    def __str__(self) -> str:
        return f"{self.product} @ {self.view}: {self.remote_id}"

    def clean(self):
        super().clean()

        tree_id = getattr(self.view, "default_category_tree_id", None)
        category_ids = {
            field_name: (getattr(self, field_name, None) or "").strip()
            for field_name in ("remote_id", "secondary_category_id")
        }
        errors = {}
        for field_name, remote_id in category_ids.items():
            if not remote_id:
                continue

            categories = EbayCategory.objects.filter(remote_id=remote_id)
            if tree_id:
                categories = categories.filter(marketplace_default_tree_id=tree_id)

            try:
                category = categories.get()
            except EbayCategory.DoesNotExist:
                errors[field_name] = "eBay category does not exist for the given remote ID."
                continue
            except EbayCategory.MultipleObjectsReturned:
                errors[field_name] = "Multiple eBay categories found for the given remote ID."
                continue

            if category.has_children:
                errors[field_name] = "Only leaf eBay categories can be assigned."

        if (
            category_ids["remote_id"]
            and category_ids["secondary_category_id"]
            and category_ids["remote_id"] == category_ids["secondary_category_id"]
        ):
            message = "Primary and secondary eBay categories cannot be the same."
            errors.setdefault("remote_id", message)
            errors.setdefault("secondary_category_id", message)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
