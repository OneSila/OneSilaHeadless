import uuid
import secrets

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError

from core import models
from integrations.models import Integration

from .constants import (
    ACTION_CHOICES,
    DELIVERY_DELIVERED,
    DELIVERY_FAILED,
    DELIVERY_PENDING,
    DELIVERY_SENDING,
    DELIVERY_STATUS_CHOICES,
    MODE_CHOICES,
    MODE_FULL,
    RETENTION_CHOICES,
    TOPIC_CHOICES,
    VERSION_2025_08_01,
    VERSION_CHOICES, RETENTION_3M,
)


def generate_secret():
    return secrets.token_hex(64)


def default_timeout_ms():
    return getattr(settings, "WEBHOOK_TIMEOUT_MS", 10000)


class WebhookIntegration(Integration):
    topic = models.CharField(max_length=32, choices=TOPIC_CHOICES)
    version = models.CharField(
        max_length=10, choices=VERSION_CHOICES, default=VERSION_2025_08_01
    )
    url = models.URLField()
    secret = models.CharField(max_length=128, default=generate_secret)
    user_agent = models.CharField(max_length=64, default="OneSila-Webhook/1.0")
    timeout_ms = models.IntegerField(default=default_timeout_ms)
    mode = models.CharField(max_length=5, choices=MODE_CHOICES, default=MODE_FULL)
    extra_headers = models.JSONField(default=dict, blank=True)
    config = models.JSONField(default=dict, blank=True)
    retention_policy = models.CharField(
        max_length=3, choices=RETENTION_CHOICES, default=RETENTION_3M
    )

    def clean(self):
        models.Model.clean(self)

    def save(self, *args, force_save=False, **kwargs):
        if self.requests_per_minute > 120:
            raise ValidationError({"requests_per_minute": "Ensure this value is less than or equal to 120."})
        super().save(*args, force_save=force_save, **kwargs)

    def regenerate_secret(self):
        self.secret = generate_secret()
        self.save(update_fields=["secret"])

    class Meta:
        indexes = [models.Index(fields=["topic"])]


class WebhookOutbox(models.Model):
    webhook_id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    webhook_integration = models.ForeignKey(WebhookIntegration, on_delete=models.CASCADE)
    topic = models.CharField(max_length=32, choices=TOPIC_CHOICES, db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    subject_type = models.CharField(max_length=32, db_index=True)
    subject_id = models.CharField(max_length=64, db_index=True)
    sequence = models.BigIntegerField(null=True, blank=True)
    payload = models.JSONField()

    class Meta:
        indexes = [
            models.Index(fields=["webhook_integration", "created_at"]),
            models.Index(fields=["topic", "created_at"]),
            models.Index(fields=["subject_type", "subject_id", "created_at"]),
        ]


class WebhookDelivery(models.Model):
    PENDING = DELIVERY_PENDING
    SENDING = DELIVERY_SENDING
    DELIVERED = DELIVERY_DELIVERED
    FAILED = DELIVERY_FAILED

    webhook_id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    outbox = models.ForeignKey(
        WebhookOutbox, on_delete=models.CASCADE, related_name="deliveries"
    )
    webhook_integration = models.ForeignKey(
        WebhookIntegration, on_delete=models.CASCADE, related_name="deliveries"
    )
    status = models.CharField(
        max_length=10,
        choices=DELIVERY_STATUS_CHOICES,
        default=DELIVERY_PENDING,
        db_index=True,
    )
    attempt = models.IntegerField(default=1, db_index=True)
    response_code = models.IntegerField(null=True, blank=True, db_index=True)
    response_ms = models.IntegerField(null=True, blank=True)
    response_body_snippet = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.response_body_snippet and len(self.response_body_snippet) > 512:
            self.response_body_snippet = self.response_body_snippet[:512]
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["outbox"],
                condition=Q(status=DELIVERY_DELIVERED),
                name="webhook_delivery_unique_delivered_per_outbox",
            )
        ]


class WebhookDeliveryAttempt(models.Model):
    delivery = models.ForeignKey(
        WebhookDelivery, on_delete=models.CASCADE, related_name="attempts"
    )
    number = models.IntegerField()
    sent_at = models.DateTimeField()
    response_code = models.IntegerField(null=True, blank=True)
    response_ms = models.IntegerField(null=True, blank=True)
    response_body_snippet = models.TextField(null=True, blank=True)
    error_text = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.response_body_snippet and len(self.response_body_snippet) > 512:
            self.response_body_snippet = self.response_body_snippet[:512]
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["delivery", "number"]),
            models.Index(fields=["delivery", "created_at"]),
        ]
