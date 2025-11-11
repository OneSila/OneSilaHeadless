"""Models representing Shein product type metadata."""

from __future__ import annotations

from django.db.models import Q

from core import models
from properties.models import ProductPropertiesRule
from sales_channels.models.mixins import RemoteObjectMixin

from .categories import SheinCategory


class SheinProductType(RemoteObjectMixin, models.Model):
    """Leaf category metadata used to map to local product rules."""

    local_instance = models.ForeignKey(
        ProductPropertiesRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local product properties rule mapped to this Shein product type.",
    )
    view = models.ForeignKey(
        "shein.SheinSalesChannelView",
        on_delete=models.CASCADE,
        related_name="product_types",
        null=True,
        blank=True,
        help_text="Shein storefront for which this product type was fetched.",
    )
    category = models.ForeignKey(
        SheinCategory,
        on_delete=models.CASCADE,
        related_name="product_types",
        help_text="Category node linked to this product type.",
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Human readable name reported by Shein for the category/product type.",
    )
    is_leaf = models.BooleanField(
        default=True,
        help_text="True when Shein marks the backing category as a last category.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original payload returned by Shein for this product type.",
    )
    imported = models.BooleanField(
        default=True,
        help_text="Indicates whether the product type was fetched from Shein.",
    )

    class Meta:
        verbose_name = "Shein Product Type"
        verbose_name_plural = "Shein Product Types"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "view", "remote_id"],
                condition=Q(remote_id__isnull=False),
                name="unique_shein_product_type_per_view",
            ),
            models.UniqueConstraint(
                fields=["category"],
                name="unique_shein_product_type_per_category",
            ),
        ]
        search_terms = ["remote_id", "name", "category__remote_id"]

    def __str__(self) -> str:
        label = self.name or self.remote_id or "Unknown"
        return f"{label} ({self.remote_id})" if self.remote_id else label
