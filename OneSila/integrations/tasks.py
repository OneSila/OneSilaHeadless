from typing import Optional, Tuple, Dict
from huey import crontab
from huey.contrib.djhuey import db_task, periodic_task, db_periodic_task

from integrations.models import IntegrationTaskQueue
import logging

logger = logging.getLogger(__name__)


@db_task()
def add_task_to_queue(
    *,
    integration_id: str | int,
    task_func_path: str,
    task_args: Optional[Tuple] = None,
    task_kwargs: Optional[Dict] = None,
    number_of_remote_requests: Optional[int] = None,
    priority: Optional[int] = None
) -> None:
    from integrations.factories.task_queue import TaskQueueFactory

    fac = TaskQueueFactory(
        integration_id=integration_id,
        task_func_path=task_func_path,
        task_args=task_args,
        task_kwargs=task_kwargs,
        number_of_remote_requests=number_of_remote_requests,
        priority=priority)

    fac.run()


@db_periodic_task(crontab(minute="*"))
def sales_channels_process_remote_tasks_queue():
    """
    Periodically process the task queue for all active integrations.
    """
    from integrations.factories.task_queue import ProcessIntegrationTasksFactory

    fac = ProcessIntegrationTasksFactory()
    fac.run()


@db_periodic_task(crontab(hour=2, minute=0, day='1,15'))
def clean_up_processed_tasks():
    deleted_count, _ = IntegrationTaskQueue.objects.filter(status=IntegrationTaskQueue.PROCESSED).delete()
    logger.info(f"Cleaned up {deleted_count} processed tasks.")
