from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from webhooks.constants import RETENTION_3M, RETENTION_6M, RETENTION_12M
from webhooks.models import (
    WebhookDelivery,
    WebhookDeliveryAttempt,
    WebhookIntegration,
    WebhookOutbox,
)


class WebhookPruneFactory:
    def __init__(self, integration: WebhookIntegration) -> None:
        self.integration = integration

    def _get_cutoff(self):
        now = timezone.now()
        policy = self.integration.retention_policy
        if policy == RETENTION_3M:
            delta = timedelta(days=90)
        elif policy == RETENTION_6M:
            delta = timedelta(days=180)
        else:
            delta = timedelta(days=365)
        return now - delta

    def run(self):
        cutoff = self._get_cutoff()
        deliveries_qs = WebhookDelivery.objects.filter(
            webhook_integration=self.integration,
            status=WebhookDelivery.DELIVERED,
            sent_at__lt=cutoff,
        )
        delivery_ids = list(deliveries_qs.values_list("id", flat=True))
        outbox_ids = list(deliveries_qs.values_list("outbox_id", flat=True))
        deliveries_count = deliveries_qs.count()
        attempts_count = WebhookDeliveryAttempt.objects.filter(
            delivery_id__in=delivery_ids
        ).count()
        deliveries_qs.delete()
        outboxes_deleted, _ = (
            WebhookOutbox.objects.filter(id__in=outbox_ids)
            .annotate(del_count=Count("deliveries"))
            .filter(del_count=0)
            .delete()
        )
        return {
            "deliveries": deliveries_count,
            "attempts": attempts_count,
            "outboxes": outboxes_deleted,
        }
