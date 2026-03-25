from __future__ import annotations

from django.core.exceptions import ValidationError

from core import models
from products.models import Product
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.models.products import RemoteProductCategory


class MiraklCategory(RemoteObjectMixin, models.Model):
    """Mirakl category tree node."""

    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Mirakl category label.",
    )
    parent_code = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Remote identifier of the parent category.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Reference to the parent category node when known.",
    )
    level = models.PositiveIntegerField(
        default=0,
        help_text="Hierarchy level reported by Mirakl.",
    )
    is_leaf = models.BooleanField(
        default=False,
        help_text="True when the category has no children in the imported tree.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original Mirakl hierarchy payload.",
    )

    class Meta:
        verbose_name = "Mirakl Category"
        verbose_name_plural = "Mirakl Categories"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_id"],
                name="unique_mirakl_category_per_channel",
            ),
        ]
        search_terms = ["remote_id", "name", "parent_code"]

    def __str__(self) -> str:
        label = self.name or self.remote_id or "Unknown"
        channel_suffix = f" @ {self.sales_channel}" if self.sales_channel_id else ""
        return f"{label}{channel_suffix}"

    def clean(self):
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "Category cannot be its own parent."})


class MiraklProductCategory(RemoteProductCategory):
    """Product to Mirakl category assignment."""

    class Meta:
        verbose_name = "Mirakl Product Category"
        verbose_name_plural = "Mirakl Product Categories"

    def clean(self):
        self.require_view = False
        super().clean()

        remote_id = (self.remote_id or "").strip()
        if not remote_id:
            return

        queryset = MiraklCategory.objects.filter(
            remote_id=remote_id,
            sales_channel=self.sales_channel,
        )
        try:
            category = queryset.get()
        except MiraklCategory.DoesNotExist as exc:
            raise ValidationError({"remote_id": "Mirakl category does not exist for the given remote ID."}) from exc
        except MiraklCategory.MultipleObjectsReturned as exc:
            raise ValidationError({"remote_id": "Multiple Mirakl categories found for the given remote ID."}) from exc

        if not category.is_leaf:
            raise ValidationError({"remote_id": "Only leaf Mirakl categories can be assigned."})

    def save(self, *args, **kwargs):
        self.require_view = False
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        product_label = getattr(self.product, "sku", None) or getattr(self.product, "name", None) or self.product_id
        return f"{product_label} @ {self.sales_channel}: {self.remote_id}"
