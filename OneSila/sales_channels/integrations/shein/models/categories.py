from core import models


class SheinCategory(models.SharedModel):
    """Represents a Shein category node shared across tenants."""

    remote_id = models.CharField(
        max_length=255,
        help_text="Identifier returned by Shein for this category.",
    )
    site_remote_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Marketplace/site identifier associated with this category tree.",
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

    class Meta:
        verbose_name = "Shein Category"
        verbose_name_plural = "Shein Categories"
        constraints = [
            models.UniqueConstraint(
                fields=["remote_id", "site_remote_id"],
                name="unique_shein_category_per_site",
            )
        ]
        search_terms = ["remote_id", "name", "parent_remote_id", "site_remote_id"]

    def __str__(self) -> str:
        site_suffix = f" @ {self.site_remote_id}" if self.site_remote_id else ""
        label = self.name or self.remote_id or "Unknown"
        return f"{label}{site_suffix}"
