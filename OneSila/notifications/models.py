from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models as django_models

from core import models


class Notification(models.Model):
    TYPE_COLLABORATION_MENTION = "COLLABORATION_MENTION"

    type = django_models.CharField(max_length=64, db_index=True)
    title = django_models.CharField(max_length=255)
    message = django_models.TextField(blank=True)
    url = django_models.CharField(max_length=2048, null=True, blank=True)
    opened = django_models.BooleanField(default=False, db_index=True)
    metadata = django_models.JSONField(default=dict, blank=True)
    user = django_models.ForeignKey(
        "core.MultiTenantUser",
        on_delete=django_models.CASCADE,
        related_name="notifications",
    )

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            django_models.Index(fields=["user", "opened"]),
            django_models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type}: {self.title}"


class CollaborationThread(models.Model):
    content_type = django_models.ForeignKey(
        ContentType,
        on_delete=django_models.CASCADE,
        related_name="notification_collaboration_threads",
    )
    object_id = django_models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    url = django_models.CharField(max_length=2048, null=True, blank=True)

    class Meta:
        ordering = ("-updated_at", "-id")
        constraints = [
            django_models.UniqueConstraint(
                fields=["multi_tenant_company", "content_type", "object_id"],
                name="notifications_collab_thread_unique_target_per_company",
            )
        ]
        indexes = [
            django_models.Index(fields=["multi_tenant_company", "content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"Collaboration for {self.content_type}:{self.object_id}"


class CollaborationEntry(models.Model):
    TYPE_COMMENT = "COMMENT"
    TYPE_ASK_APPROVAL = "ASK_APPROVAL"
    TYPE_APPROVED = "APPROVED"
    TYPE_REJECTED = "REJECTED"

    TYPE_CHOICES = (
        (TYPE_COMMENT, "Comment"),
        (TYPE_ASK_APPROVAL, "Ask approval"),
        (TYPE_APPROVED, "Approved"),
        (TYPE_REJECTED, "Rejected"),
    )

    thread = django_models.ForeignKey(
        CollaborationThread,
        on_delete=django_models.CASCADE,
        related_name="entries",
    )
    type = django_models.CharField(max_length=64, choices=TYPE_CHOICES, db_index=True)
    comment = django_models.TextField(null=True, blank=True)
    metadata = django_models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            django_models.Index(fields=["thread", "created_at"]),
            django_models.Index(fields=["type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} on thread {self.thread_id}"


class CollaborationMention(models.Model):
    entry = django_models.ForeignKey(
        CollaborationEntry,
        on_delete=django_models.CASCADE,
        related_name="mentions",
    )
    user = django_models.ForeignKey(
        "core.MultiTenantUser",
        on_delete=django_models.CASCADE,
        related_name="collaboration_mentions",
    )

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            django_models.UniqueConstraint(
                fields=["entry", "user"],
                name="notifications_collab_mention_unique_entry_user",
            )
        ]
        indexes = [
            django_models.Index(fields=["user", "created_at"]),
        ]

    def clean(self):
        super().clean()

        entry_company_id = getattr(self.entry, "multi_tenant_company_id", None)
        user_company_id = getattr(self.user, "multi_tenant_company_id", None)

        if self.multi_tenant_company_id and entry_company_id and self.multi_tenant_company_id != entry_company_id:
            raise ValidationError({"entry": "Mention entry must belong to the same company."})

        if self.multi_tenant_company_id and user_company_id and self.multi_tenant_company_id != user_company_id:
            raise ValidationError({"user": "Mentioned user must belong to the same company."})

        if entry_company_id and user_company_id and entry_company_id != user_company_id:
            raise ValidationError({"user": "Mentioned user must belong to the entry company."})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Mention {self.user_id} on entry {self.entry_id}"
