import logging
from datetime import datetime
from typing import Optional, Tuple, Dict

from django.core.exceptions import ValidationError
from django.db.models import Sum

from core.huey import DEFAULT_PRIORITY
from integrations.helpers import resolve_function
from integrations.models import IntegrationTaskQueue, Integration

logger = logging.getLogger(__name__)

class TaskQueueFactory:
    def __init__(self,
                 integration_id: str | int,
                 task_func_path: str,
                 task_args: Optional[Tuple] = None,
                 task_kwargs: Optional[Dict] = None,
                 number_of_remote_requests: Optional[int] = None,
                 priority: Optional[int] = None):

        self.integration_id = integration_id
        self.task_func_path = task_func_path
        self.task_args = task_args or ()
        self.task_kwargs = task_kwargs or {}
        self.number_of_remote_requests = number_of_remote_requests
        self.priority = priority

        # Initialize without setting until run method
        self.integration = None
        self.task_func = None
        self.remote_requests = None
        self.active_requests = None
        self.process_now = None
        self.task_queue_item = None

    def set_integration(self):
        """
        Set the integration based on the integration_id.
        """
        self.integration = Integration.objects.get(id=self.integration_id)

    def set_task_func(self):
        """
        Resolve the task function and set it.
        """
        task_func = resolve_function(self.task_func_path)
        if not callable(task_func):
            raise ValidationError("The provided task function is not callable.")

        self.task_func = task_func

    def set_remote_requests(self):
        """
        Determine and set the number of remote requests for the task.
        """
        self.remote_requests = self.number_of_remote_requests if self.number_of_remote_requests is not None else getattr(self.task_func, 'number_of_remote_requests', 1)

    def set_active_requests(self):
        """
        Get and set the total number of currently active requests for the integration.
        """
        self.active_requests = IntegrationTaskQueue.objects.filter(
            integration=self.integration,
            status__in=[IntegrationTaskQueue.PROCESSING, IntegrationTaskQueue.PENDING]
        ).aggregate(total=Sum('number_of_remote_requests'))['total'] or 0

    def set_process_now(self):
        """
        Determine if the task should be processed immediately based on the requests per minute limit and set it.
        """
        self.process_now = self.active_requests + self.remote_requests <= self.integration.requests_per_minute

    def _get_task_priority(self):
        """
        Get the priority of the task, either from provided value or default to the task function's priority.
        """
        return self.priority if self.priority is not None else getattr(self.task_func, 'priority', DEFAULT_PRIORITY)

    def _get_task_status(self):
        """
        Determine the status of the task based on whether it should be processed immediately or queued.
        """
        return IntegrationTaskQueue.PROCESSING if self.process_now else IntegrationTaskQueue.PENDING

    def create_task_queue_item(self):
        """
        Create the IntegrationTaskQueue entry and set it as a class attribute.
        """
        task_status = self._get_task_status()
        task_priority = self._get_task_priority()

        logger.debug(
            f"Task for Integration '{self.integration.hostname}': Requests per minute limit is {self.integration.requests_per_minute}. "
            f"Currently active requests: {self.active_requests}. Processing now: {self.process_now}.")

        self.task_queue_item = IntegrationTaskQueue.objects.create(
            integration=self.integration,
            task_name=self.task_func_path,
            task_args=self.task_args,
            task_kwargs=self.task_kwargs,
            status=task_status,
            number_of_remote_requests=self.remote_requests,
            priority=task_priority,
            multi_tenant_company=self.integration.multi_tenant_company
        )

        logger.debug(
            f"Task '{self.task_func_path}' {'immediately processing' if self.process_now else 'added to the queue'} for Integration '{self.integration.hostname}' "
            f"with priority {task_priority}.")

    def dispatch_task(self):
        """
        Dispatch the task if conditions allow, using the created task_queue_item.
        """
        if self.process_now and self.task_queue_item:
            self.task_queue_item.dispatch()

    def run(self):
        """
        Run the full process: set attributes, create the task, and dispatch it.
        """
        self.set_integration()
        self.set_task_func()
        self.set_remote_requests()
        self.set_active_requests()
        self.set_process_now()
        self.create_task_queue_item()
        self.dispatch_task()


class ProcessIntegrationTasksFactory:
    def __init__(self):
        self.integrations = Integration.objects.filter(active=True)

    def get_pending_tasks(self, integration):
        """
        Get the pending tasks for the current integration.
        """
        pending_tasks = IntegrationTaskQueue.get_pending_tasks(integration)
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Found {len(pending_tasks)} tasks to process for Integration '{integration.hostname}' "
            f"with a limit of {integration.requests_per_minute} requests per minute."
        )
        return pending_tasks

    def dispatch_tasks(self, integration, pending_tasks):
        """
        Dispatch the pending tasks for the current integration.
        If the integration is inactive, mark tasks as skipped.
        """
        if not integration.active:

            for task in pending_tasks:
                task.status = IntegrationTaskQueue.SKIPPED

            IntegrationTaskQueue.objects.bulk_update(pending_tasks, ['status'])
            logger.info(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Integration '{integration.hostname}' is inactive — skipped {len(pending_tasks)} task(s)."
            )
            return

        # If active, continue with normal dispatch
        for task_queue_item in pending_tasks:
            task_queue_item.dispatch()
            logger.info(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Dispatched task '{task_queue_item.task_name}' for Integration '{integration.hostname}'"
            )

    def run(self):
        """
        Run the process for all active integrations: get pending tasks and dispatch them.
        """
        for integration in self.integrations:
            pending_tasks = self.get_pending_tasks(integration)
            self.dispatch_tasks(integration, pending_tasks)