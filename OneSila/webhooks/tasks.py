from huey.contrib.djhuey import db_task

from integrations.factories.remote_task import BaseRemoteTask
from sales_channels.decorators import remote_task
from webhooks.factories import SendWebhookDeliveryFactory


# !IMPORTANT: @remote_task needs to be above in order to work
@remote_task()
@db_task()
def send_webhook_delivery(task_queue_item_id, outbox_id: int, delivery_id: int) -> None:
    task = BaseRemoteTask(task_queue_item_id)

    def actual_task() -> None:
        factory = SendWebhookDeliveryFactory(outbox_id=outbox_id, delivery_id=delivery_id)
        factory.run()

    task.execute(actual_task)
