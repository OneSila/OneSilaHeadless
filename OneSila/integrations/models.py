from django.core.exceptions import ValidationError
from polymorphic.models import PolymorphicModel
from core import models
import logging
from django.utils.timezone import now
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.huey import DEFAULT_PRIORITY
import json
from datetime import datetime

logger = logging.getLogger(__name__)



class Integration(PolymorphicModel, models.Model):
    """
    Polymorphic model representing a integration like sales channel, such as a website or marketplace or accounting accounts.
    """
    hostname = models.URLField()
    active = models.BooleanField(default=True)
    verify_ssl = models.BooleanField(default=True)
    requests_per_minute = models.IntegerField(default=60)
    internal_company = models.ForeignKey('contacts.Company',on_delete=models.PROTECT)

    class Meta:
        unique_together = ('multi_tenant_company', 'hostname')
        verbose_name = 'Integration'
        verbose_name_plural = 'Integrations'


    def __str__(self):
        return f"{self.hostname} @ {self.multi_tenant_company}"

class IntegrationTaskQueue(models.Model):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'  # New status
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
        (FAILED, 'Failed'),  # New status choice
    ]

    integration = models.ForeignKey(Integration, null=True, blank=True, on_delete=models.SET_NULL)
    task_name = models.CharField(max_length=255)
    task_args = models.JSONField(null=True, blank=True)
    task_kwargs = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    sent_to_queue_at = models.DateTimeField(default=now)
    retry = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)
    error_history = models.JSONField(default=dict, blank=True)
    number_of_remote_requests = models.IntegerField(default=1) # how many remote requests does this task do?
    priority = models.IntegerField(default=DEFAULT_PRIORITY)

    @property
    def name(self):
        """Extracts the simplified task name from the task path."""
        return self.task_name.split('.')[-1]

    def __str__(self):
        hostname = self.integration.hostname if self.integration else "N/A"
        return f"{self.name} > {hostname}"

    @classmethod
    def get_pending_tasks(cls, integration):
        # Sum the number of remote requests for currently processing tasks
        processing_requests = cls.objects.filter(
            integration=integration,
            status=cls.PROCESSING
        ).aggregate(total=models.Sum('number_of_remote_requests'))['total'] or 0

        # Calculate the number of requests that can still be processed
        remaining_requests = integration.requests_per_minute - processing_requests

        if remaining_requests > 0:
            # Get pending tasks, ordered by priority (high first) then by sent_to_queue_at
            pending_tasks = cls.objects.filter(
                integration=integration,
                status=cls.PENDING
            ).order_by('-priority', 'sent_to_queue_at')

            # Select tasks until the sum of their remote requests fits the remaining capacity
            selected_tasks = []
            total_requests = 0

            for task in pending_tasks:
                task_requests = task.number_of_remote_requests

                # if a task is bigger than the limit just add it. It will keep the queue full until is finished but at least will be processed
                if task_requests > integration.requests_per_minute:
                    task.status = cls.PROCESSING
                    selected_tasks.append(task)
                    break

                if total_requests + task_requests <= remaining_requests:
                    task.status = cls.PROCESSING
                    selected_tasks.append(task)
                    total_requests += task_requests
                else:
                    break

            if selected_tasks:
                cls.objects.bulk_update(selected_tasks, ['status'])
            return selected_tasks

        return []

    def mark_as_processed(self):
        self.status = self.PROCESSED
        self.save()

    def mark_as_failed(self, error_message=None, error_traceback=None):
        self.retry += 1
        if self.retry < 3:
            self.status = self.PENDING
            self.sent_to_queue_at = now()
        else:
            self.status = self.FAILED

        next_key = str(len(self.error_history))

        error_entry = {
            'retry': self.retry,
            'message': error_message,
            'traceback': error_traceback,
            'timestamp': str(now()),
        }
        self.error_history[next_key] = error_entry

        self.error_message = error_message
        self.error_traceback = error_traceback

        self.save()

    def dispatch(self):
        from integrations.helpers import resolve_function

        if self.status != self.PROCESSING:
            raise ValidationError("Cannot dispatch not proccessing tasks.")

        task_func = resolve_function(self.task_name)

        if task_func:
            logger.info(f"Dispatching task '{self.task_name}' for SalesChannel '{self.integration.hostname}'.")
            # Pass task_queue_item_id, integration_id, and relevant args to the task
            return task_func(
                self.id,
                *self.task_args,
                **self.task_kwargs
            )
        else:
            logger.error(f"Task '{self.task_name}' not found.")

    def retry_task(self, retry_now=False):
        self.retry = 0

        self.status = self.PROCESSING if retry_now else self.PENDING
        self.sent_to_queue_at = now()
        self.save()

        if retry_now:
            self.dispatch()


class IntegrationLog(PolymorphicModel, models.Model):
    """
    A generic log model to track actions related to various objects in the system.
    All the models that will have RemoteObjectMixin will have special methods to create this logs for EVERY SINGLE API REQUEST
    This gives us full control over any error / any api request that was made from our system and full traceability
    """

    # Constants for action choices
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]

    # Constants for status choices
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    integration = models.ForeignKey(Integration, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)
    payload = models.JSONField(null=True, blank=True, help_text="The API call payload associated with this log.")
    response = models.TextField(null=True, blank=True, help_text="The API response or additional information.")
    error_traceback = models.TextField(null=True, blank=True, help_text="Detailed error traceback if the action failed.")
    user_error = models.BooleanField(default=False)  # Boolean field to indicate if the error is user-facing
    identifier = models.CharField(max_length=255, null=True, blank=True)  # Field to store a unique identifier for the log entry
    keep = models.BooleanField(default=False, help_text="Whether to keep this log permanently.")
    related_object_str = models.CharField(max_length=556, null=True, blank=True, help_text="String representation of the related object.")

    class Meta:
        verbose_name = 'Integration Log'
        verbose_name_plural = 'Integration Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Log for {self.content_object} - Action: {self.action}, Status: {self.status}"
    
    

class IntegrationObjectMixin(models.Model):
    """
    Mixin that adds a remote_id field to track objects in remote systems,
    a integration reference, and provides methods for logging related actions.
    Also includes a successfully_created field to track if the object was
    successfully created in the remote system.
    """

    remote_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of the object in the remote system")
    # if a mirror model was created but it fails next time we update it we will try update method because mirror model was created
    # to avoid that we have this field
    successfully_created = models.BooleanField(default=True, help_text="Indicates if the object was successfully created in the remote system.")

    # this should be overriden in the save we should make a qs on the logs to all the different identifier of the latest versions
    # they all need to be success for this to be true
    outdated = models.BooleanField(default=False, help_text="Indicates if the remote product is outdated due to an error.")
    outdated_since = models.DateTimeField(null=True, blank=True, help_text="Timestamp indicating when the object became outdated.")


    class Meta:
        abstract = True

    @property
    def integration(self):
        """
        Abstract integration property to be overridden by subclasses.
        Must return the relevant integration (e.g., sales_channel or accounting account).
        """
        raise NotImplementedError("Subclasses must override the 'integration' property.")

    @property
    def safe_str(self):
        return f'To be deleted {self.remote_id}'


    @property
    def errors(self):
        """
        Retrieve the latest errors based on unique identifiers.
        Only includes errors that are the latest occurrence of their identifier.
        """
        content_type = ContentType.objects.get_for_model(self)
        # Fetch the latest logs for each identifier
        latest_logs = IntegrationLog.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            status=IntegrationLog.STATUS_FAILED
        ).order_by('identifier', '-created_at').distinct('identifier')

        # Return only logs with a FAILED status
        return latest_logs.filter(status=IntegrationLog.STATUS_FAILED)

    @property
    def payload(self):
        """
        Get the payload of the last log entry.
        """
        content_type = ContentType.objects.get_for_model(self)
        last_log = IntegrationLog.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            status=IntegrationLog.STATUS_SUCCESS
        ).order_by('-created_at').first()
        return last_log.payload if last_log else {}

    def add_log(self, action, response, payload, identifier,  **kwargs):
        """
        Method to add a successful log entry.
        """
        self.create_log_entry(
            action=action,
            status=IntegrationLog.STATUS_SUCCESS,
            response=response,
            payload=payload,
            identifier=identifier,
           **kwargs
        )

    def add_error(self, action, response, payload, error_traceback, identifier, user_error=False, **kwargs):
        """
        Method to add an error log entry.
        """
        self.create_log_entry(
            action=action,
            status=IntegrationLog.STATUS_FAILED,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            identifier=identifier,
            user_error=user_error,
            **kwargs
        )

    def add_user_error(self, action, response, payload, error_traceback, identifier, **kwargs):
        """
        Method to add a user-facing error log entry.
        """
        self.add_error(
            action=action,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            identifier=identifier,
            user_error=True,
            **kwargs
        )

    def add_admin_error(self, action, response, payload, error_traceback, identifier, **kwargs):
        """
        Method to add an admin-facing error log entry.
        """
        self.add_error(
            action=action,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            identifier=identifier,
            user_error=False,
            **kwargs
        )

    def create_log_entry(self, action, status, response, payload, error_traceback=None, identifier=None, user_error=False, **kwargs):
        """
        Method to create a log entry.
        """
        IntegrationLog.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            content_object=self,
            integration=self.integration,
            action=action,
            status=status,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            identifier=identifier,
            user_error=user_error,
            multi_tenant_company=self.integration.multi_tenant_company,
            related_object_str=str(self),
            **kwargs
        )

    def need_update(self, new_payload):
        """
        Compares the current payload with a new one to determine if an update is needed.
        """
        current_payload = self.payload
        return json.dumps(current_payload, sort_keys=True) != json.dumps(new_payload, sort_keys=True)

    def mark_outdated(self, save=True):
        """
        Marks the object as outdated due to an error and sets the outdated_since timestamp.
        """
        self.outdated = True
        self.outdated_since = datetime.now()
        if save:
            self.save()

    def save(self, *args, **kwargs):
        """
        Overrides save method to check for errors and mark as outdated if necessary.
        """
        # Check if there are any errors
        if self.errors.exists():
            self.mark_outdated(save=False)  # Mark as outdated without saving immediately
        else:
            # Reset outdated status if no errors are found
            self.outdated = False
            self.outdated_since = None

        # Call the original save method
        super().save(*args, **kwargs)