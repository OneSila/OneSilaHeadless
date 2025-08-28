import logging
from huey import crontab
from huey.contrib.djhuey import db_task, db_periodic_task

from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.decorators import remote_task
from webhooks.factories import SendWebhookDeliveryFactory
from webhooks.factories.prune_deliveries import WebhookPruneFactory
from webhooks.models import WebhookIntegration

logger = logging.getLogger(__name__)


# !IMPORTANT: @remote_task needs to be above in order to work
@remote_task()
@db_task()
def send_webhook_delivery(task_queue_item_id, outbox_id: int, delivery_id: int) -> None:
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = SendWebhookDeliveryFactory(outbox_id=outbox_id, delivery_id=delivery_id)
        factory.run()

    task.execute(actual_task)


@db_periodic_task(crontab(day='*', hour='0', minute='0'))
def webhooks__prune_old_deliveries__cronjob() -> None:
    for integration in WebhookIntegration.objects.filter(active=True):
        counts = WebhookPruneFactory(integration=integration).run()
        logger.info(
            "Integration %s pruned %s deliveries, %s attempts, %s outboxes",
            integration.id,
            counts["deliveries"],
            counts["attempts"],
            counts["outboxes"],
        )
