from django.utils import timezone

from integrations.tasks import add_task_to_queue

from webhooks.models import WebhookDelivery


class ReplayDelivery:
    """Utility to replay a webhook delivery."""

    def __init__(self, delivery: WebhookDelivery) -> None:
        self.delivery = delivery

    def _reset(self) -> None:
        self.delivery.status = WebhookDelivery.PENDING
        self.delivery.attempt += 1
        self.delivery.save(update_fields=["status", "attempt"])

    def _log_attempt(self) -> None:
        self.delivery.attempts.create(
            number=self.delivery.attempt,
            sent_at=timezone.now(),
            multi_tenant_company=self.delivery.multi_tenant_company,
        )

    def _enqueue(self) -> None:
        add_task_to_queue(
            integration_id=self.delivery.webhook_integration_id,
            task_func_path="webhooks.tasks.process_delivery",
            task_kwargs={"delivery_id": self.delivery.id},
        )

    def run(self) -> None:
        self._reset()
        self._log_attempt()
        self._enqueue()
