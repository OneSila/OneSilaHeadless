from django.contrib import admin

from core.admin import ModelAdmin

from .models import (
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookIntegration,
    WebhookOutbox,
)


@admin.register(WebhookIntegration)
class WebhookIntegrationAdmin(ModelAdmin):
    list_display = ["hostname", "url", "topic", "version", "active"]
    list_filter = ["topic", "version", "active"]


@admin.register(WebhookOutbox)
class WebhookOutboxAdmin(ModelAdmin):
    list_display = [
        "webhook_id",
        "webhook_integration",
        "topic",
        "action",
        "subject_type",
        "subject_id",
        "created_at",
    ]
    list_filter = ["webhook_integration", "topic", "action", "subject_type"]


@admin.action(description="Replay selected deliveries")
def replay_deliveries(modeladmin, request, queryset):
    queryset.update(
        status=WebhookDelivery.PENDING,
        attempt=0,
        response_code=None,
        response_ms=None,
        response_body_snippet=None,
        sent_at=None,
        error_message=None,
        error_traceback=None,
    )


class WebhookDeliveryAttemptInline(admin.TabularInline):
    model = WebhookDeliveryAttempt
    extra = 0
    readonly_fields = [
        "number",
        "sent_at",
        "response_code",
        "response_ms",
        "response_body_snippet",
        "error_text",
        "error_traceback",
    ]


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(ModelAdmin):
    list_display = [
        "webhook_id",
        "webhook_integration",
        "status",
        "attempt",
        "response_code",
        "sent_at",
    ]
    list_filter = ["status", "webhook_integration", "response_code"]
    actions = [replay_deliveries]
    inlines = [WebhookDeliveryAttemptInline]


@admin.register(WebhookDeliveryAttempt)
class WebhookDeliveryAttemptAdmin(ModelAdmin):
    list_display = ["delivery", "number", "sent_at", "response_code"]
    list_filter = ["response_code"]
