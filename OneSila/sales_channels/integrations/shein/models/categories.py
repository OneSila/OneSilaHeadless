from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError

from core import models
from products.models import Product
from sales_channels.models import SalesChannel


class SheinCategory(models.Model):
    """Represents a Shein category node scoped to a Shein sales channel."""

    remote_id = models.CharField(
        max_length=255,
        help_text="Identifier returned by Shein for this category.",
    )
    sales_channel = models.ForeignKey(
        SalesChannel,
        on_delete=models.CASCADE,
        help_text="Sales channel that owns this category tree.",
    )
    parent_remote_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Identifier of the parent category according to Shein.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Reference to the parent category node when available.",
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Display name for the category.",
    )
    is_leaf = models.BooleanField(
        default=False,
        help_text="True when Shein marks the category as a last category.",
    )
    product_type_remote_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Product type identifier associated with the category, if any.",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original payload returned by Shein for this category (without children).",
    )
    default_language = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Default mandatory language configured by Shein for this category.",
    )
    currency = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Currency that Shein expects for supply prices in this category.",
    )
    reference_info_required = models.BooleanField(
        default=False,
        help_text="Indicates whether Shein marks the reference info module as required for publishing.",
    )
    reference_product_link_required = models.BooleanField(
        default=False,
        help_text="Indicates whether a competitor product link is mandatory when publishing.",
    )
    proof_of_stock_required = models.BooleanField(
        default=False,
        help_text="Indicates whether proof of stock is mandatory when publishing.",
    )
    shelf_require_required = models.BooleanField(
        default=False,
        help_text="Indicates whether shelf requirements must be provided when publishing.",
    )
    brand_code_required = models.BooleanField(
        default=False,
        help_text="Indicates whether a brand code is mandatory when publishing.",
    )
    skc_title_required = models.BooleanField(
        default=False,
        help_text="Indicates whether the SKC title is mandatory when publishing.",
    )
    minimum_stock_quantity_required = models.BooleanField(
        default=False,
        help_text="Indicates whether a minimum stock quantity is mandatory when publishing.",
    )
    product_detail_picture_required = models.BooleanField(
        default=False,
        help_text="Indicates whether detailed product images are mandatory when publishing.",
    )
    quantity_info_required = models.BooleanField(
        default=False,
        help_text="Indicates whether SKU quantity information must be provided when publishing.",
    )
    sample_spec_required = models.BooleanField(
        default=False,
        help_text="Indicates whether sample information is mandatory when publishing.",
    )
    picture_config = models.JSONField(
        default=list,
        blank=True,
        help_text="Picture configuration flags returned by Shein for this category.",
    )
    support_sale_attribute_sort = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether sales attributes can be sorted (as reported by Shein).",
    )
    package_type_required = models.BooleanField(
        default=False,
        help_text="Indicates whether Shein requires package type information for publishing.",
    )
    supplier_barcode_required = models.BooleanField(
        default=False,
        help_text="Indicates whether Shein requires supplier barcode information for publishing.",
    )

    class Meta:
        verbose_name = "Shein Category"
        verbose_name_plural = "Shein Categories"
        constraints = [
            models.UniqueConstraint(
                fields=["sales_channel", "remote_id"],
                name="unique_shein_category_per_channel",
            )
        ]
        search_terms = ["remote_id", "name", "parent_remote_id"]

    def __str__(self) -> str:
        label = self.name or self.remote_id or "Unknown"
        channel_suffix = f" @ {self.sales_channel}" if self.sales_channel_id else ""
        return f"{label}{channel_suffix}"

    def get_publish_standard(self, *, default: Any | None = None) -> dict[str, Any]:
        raw_data = self.raw_data or {}
        if not isinstance(raw_data, dict):
            return default if isinstance(default, dict) else {}

        publish_standard = raw_data.get("publish_standard")
        if isinstance(publish_standard, dict):
            return publish_standard

        return default if isinstance(default, dict) else {}

    @property
    def properties(self) -> list[dict[str, Any]]:
        publish_standard = self.get_publish_standard(default={})
        properties = publish_standard.get("properties")
        if not isinstance(properties, list):
            properties = publish_standard.get("configurator_properties")
        if isinstance(properties, list):
            return [entry for entry in properties if isinstance(entry, dict)]
        return []


class SheinProductCategory(models.Model):
    """Link a product to a recommended Shein category per sales channel."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    remote_id = models.CharField(max_length=255)
    product_type_remote_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional Shein product type identifier for this category selection.",
    )

    class Meta:
        unique_together = ("product", "sales_channel")
        verbose_name = "Shein Product Category"
        verbose_name_plural = "Shein Product Categories"
        search_terms = ["remote_id", "product_type_remote_id", "product__sku"]

    def __str__(self) -> str:
        type_suffix = f" ({self.product_type_remote_id})" if self.product_type_remote_id else ""
        return f"{self.product} @ {self.sales_channel}: {self.remote_id}{type_suffix}"

    def clean(self):
        super().clean()

        remote_id = (self.remote_id or "").strip()
        if not remote_id:
            return

        queryset = SheinCategory.objects.filter(remote_id=remote_id)
        if self.sales_channel_id:
            queryset = queryset.filter(sales_channel=self.sales_channel)

        try:
            category = queryset.get()
        except SheinCategory.DoesNotExist as exc:
            raise ValidationError({"remote_id": "Shein category does not exist for the given remote ID."}) from exc
        except SheinCategory.MultipleObjectsReturned as exc:
            raise ValidationError(
                {
                    "remote_id": "Multiple Shein categories found for the given remote ID.",
                }
            ) from exc

        if not category.is_leaf:
            raise ValidationError({"remote_id": "Only leaf Shein categories can be assigned."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
