from __future__ import annotations

from typing import Optional

from django.db import models as django_models
from get_absolute_url.helpers import generate_absolute_url
from polymorphic.models import PolymorphicModel

from core import models
from core.upload_paths import tenant_upload_to


class SalesChannelFeed(PolymorphicModel, models.Model):
    """Reusable batch artifact for feed-style integrations."""

    STATUS_NEW = "new"
    STATUS_PENDING = "pending"
    STATUS_SUBMITTED = "submitted"
    STATUS_PROCESSING = "processing"
    STATUS_SUCCESS = "success"
    STATUS_PARTIAL = "partial"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    CONCLUDED_STATUSES = (
        STATUS_SUCCESS,
        STATUS_PARTIAL,
        STATUS_FAILED,
        STATUS_CANCELLED,
    )

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PENDING, "Pending"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    sales_channel = models.ForeignKey(
        "sales_channels.SalesChannel",
        on_delete=models.CASCADE,
        related_name="feed_batches",
    )
    type = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default=STATUS_NEW)
    remote_id = models.CharField(max_length=255, blank=True, default="")
    file = models.FileField(
        upload_to=tenant_upload_to("sales_channel_feeds"),
        null=True,
        blank=True,
        help_text="Generated file uploaded to the remote integration when applicable.",
    )
    payload_data = models.JSONField(default=list, blank=True)
    items_count = models.PositiveIntegerField(default=0)
    rows_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_submitted_at = models.DateTimeField(null=True, blank=True)
    last_polled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            django_models.Index(fields=["sales_channel", "type", "status"]),
        ]
        verbose_name = "Sales Channel Feed"
        verbose_name_plural = "Sales Channel Feeds"

    def __str__(self) -> str:
        return f"{self.sales_channel} {self.type} feed #{self.pk or 'new'}"

    @classmethod
    def get_gathering_status_for_type(cls, *, feed_type: str) -> str:
        raise NotImplementedError(f"{cls.__name__} must define get_gathering_status_for_type().")

    @property
    def file_url(self) -> Optional[str]:
        if not self.file:
            return None
        try:
            return f"{generate_absolute_url(trailing_slash=False)}{self.file.url}"
        except ValueError:
            return None


class SalesChannelFeedItem(models.Model):
    """Product-level result row within a feed batch."""

    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    feed = models.ForeignKey(
        "sales_channels.SalesChannelFeed",
        on_delete=models.CASCADE,
        related_name="items",
    )
    remote_product = models.ForeignKey(
        "sales_channels.RemoteProduct",
        on_delete=models.CASCADE,
        related_name="feed_items",
    )
    sales_channel_view = models.ForeignKey(
        "sales_channels.SalesChannelView",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feed_items",
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES, default=ACTION_UPDATE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    identifier = models.CharField(max_length=255, blank=True, default="")
    payload_data = models.JSONField(default=dict, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]
        constraints = [
            django_models.UniqueConstraint(
                fields=["feed", "remote_product", "sales_channel_view"],
                name="uniq_sales_channel_feed_item_per_remote_product",
                nulls_distinct=False,
            ),
        ]
        indexes = [
            django_models.Index(fields=["feed", "status"]),
            django_models.Index(fields=["remote_product", "status"]),
        ]
        verbose_name = "Sales Channel Feed Item"
        verbose_name_plural = "Sales Channel Feed Items"

    def __str__(self) -> str:
        identifier = self.identifier or getattr(self.remote_product, "remote_sku", "") or self.remote_product_id
        return f"{self.feed_id}:{identifier}"
