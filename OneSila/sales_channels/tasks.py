from typing import Callable, Optional, Tuple, Dict

from django.db.models import Sum
from huey import crontab
from huey.contrib.djhuey import db_task, periodic_task
from django.core.exceptions import ValidationError
import logging

from core.huey import DEFAULT_PRIORITY
from sales_channels.models.sales_channels import SalesChannel, RemoteTaskQueue

logger = logging.getLogger(__name__)


@db_task()
def add_task_to_queue(
    *,
    sales_channel_id: str | int,
    task_func: Callable,
    task_args: Optional[Tuple] = None,
    task_kwargs: Optional[Dict] = None,
    number_of_remote_requests: int = 1
) -> None:

    sales_channel = SalesChannel.objects.get(id=sales_channel_id)

    # Validate the task function
    if not callable(task_func):
        raise ValidationError("The provided task function is not callable.")

    # Check the total number of currently active requests (in PROCESSING and PENDING status)
    active_requests = RemoteTaskQueue.objects.filter(
        sales_channel=sales_channel,
        status__in=[RemoteTaskQueue.PROCESSING, RemoteTaskQueue.PENDING]
    ).aggregate(total=Sum('number_of_remote_requests'))['total'] or 0

    # Determine whether to process the task immediately based on requests per minute limit
    process_now = active_requests + number_of_remote_requests <= sales_channel.requests_per_minute

    task_priority = getattr(task_func, 'settings', {}).get('default_priority', DEFAULT_PRIORITY)

    logger.debug(
        f"Task for SalesChannel '{sales_channel.name}': Requests per minute limit is {sales_channel.requests_per_minute}. Currently active requests: {active_requests}. Processing now: {process_now}.")

    # Set task status based on whether it should be processed immediately or queued
    task_status = RemoteTaskQueue.PROCESSING if process_now else RemoteTaskQueue.PENDING

    # Create the RemoteTaskQueue entry with the appropriate parameters
    task_queue_item = RemoteTaskQueue.objects.create(
        sales_channel=sales_channel,
        task_name=task_func.__name__,
        task_args=task_args or {},
        task_kwargs=task_kwargs or {},
        status=task_status,
        number_of_remote_requests=number_of_remote_requests,
        priority=task_priority,
        multi_tenant_company=sales_channel.multi_tenant_company
    )

    logger.debug(
        f"Task '{task_func.__name__}' {'immediately processing' if process_now else 'added to the queue'} for SalesChannel '{sales_channel.name}' with priority {priority}.")

    # Dispatch the task immediately if conditions allow
    if process_now:
        task_queue_item.dispatch()


@periodic_task(crontab(minute="*"))
def process_task_queue():
    for sales_channel in SalesChannel.objects.filter(active=True):
        # Get the next batch of tasks that can be processed
        pending_tasks = RemoteTaskQueue.get_pending_tasks(sales_channel)

        # Log the number of pending tasks found and the request limit
        logger.info(f"Found {len(pending_tasks)} tasks to process for SalesChannel '{sales_channel.name}' with a limit of {sales_channel.requests_per_minute} requests per minute.")

        # Dispatch each task in the batch
        for task_queue_item in pending_tasks:
            task_queue_item.dispatch()

@periodic_task(crontab(hour=0, minute=0))  # Run this every day at midnight
def clean_up_processed_tasks():
    deleted_count, _ = RemoteTaskQueue.objects.filter(status=RemoteTaskQueue.PROCESSED).delete()
    logger.info(f"Cleaned up {deleted_count} processed tasks.")