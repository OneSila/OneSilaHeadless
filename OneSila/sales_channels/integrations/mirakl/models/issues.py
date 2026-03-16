from __future__ import annotations

from core import models


class MiraklProductIssue(models.Model):
    """Persist Mirakl product warnings and errors for matched remote products."""

    remote_product = models.ForeignKey(
        "mirakl.MiraklProduct",
        on_delete=models.CASCADE,
        related_name="issues",
        help_text="The Mirakl remote product this issue refers to.",
    )
    views = models.ManyToManyField(
        "mirakl.MiraklSalesChannelView",
        related_name="product_issues",
        blank=True,
        help_text="Mirakl channels where this issue applies, when provided by the API.",
    )
    main_code = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=255, null=True, blank=True)
    reason_label = models.CharField(max_length=255, null=True, blank=True)
    attribute_code = models.CharField(max_length=255, null=True, blank=True)
    is_rejected = models.BooleanField(default=False, db_index=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Mirakl Product Issue"
        verbose_name_plural = "Mirakl Product Issues"
        ordering = ("remote_product_id", "main_code", "code", "id")
        search_terms = ("main_code", "code", "message", "severity", "reason_label", "attribute_code")

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.remote_product_id}:{self.code or self.main_code}"
