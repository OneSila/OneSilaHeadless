"""Public Shein category tree representation."""

from __future__ import annotations

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
