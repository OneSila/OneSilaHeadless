from core import models
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime

class RemoteObjectMixin(models.Model):
    """
    Mixin that adds a remote_id field to track objects in remote systems,
    a sales_channel reference, and provides methods for logging related actions.
    Also includes a successfully_created field to track if the object was
    successfully created in the remote system.
    """

    remote_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of the object in the remote system")
    sales_channel = models.ForeignKey('sales_channels.SalesChannel', on_delete=models.PROTECT, db_index=True)
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
    def safe_str(self):
        return f'To be deleted {self.remote_id}'


    @property
    def errors(self):
        """
        Retrieve the latest errors based on unique identifiers.
        Only includes errors that are the latest occurrence of their identifier.
        """
        from .logs import RemoteLog
        content_type = ContentType.objects.get_for_model(self)
        # Fetch the latest logs for each identifier
        latest_logs = RemoteLog.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            status=RemoteLog.STATUS_FAILED
        ).order_by('identifier', '-created_at').distinct('identifier')

        # Return only logs with a FAILED status
        return latest_logs.filter(status=RemoteLog.STATUS_FAILED)

    @property
    def payload(self):
        """
        Get the payload of the last log entry.
        """
        from .logs import RemoteLog
        content_type = ContentType.objects.get_for_model(self)
        last_log = RemoteLog.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).order_by('-created_at').first()
        return last_log.payload if last_log else {}

    def add_log(self, action, response, payload, identifier,  **kwargs):
        from .logs import RemoteLog

        """
        Method to add a successful log entry.
        """
        self.create_log_entry(
            action=action,
            status=RemoteLog.STATUS_SUCCESS,
            response=response,
            payload=payload,
            identifier=identifier,
           **kwargs
        )

    def add_error(self, action, response, payload, error_traceback, identifier, user_error=False, **kwargs):
        from .logs import RemoteLog
        """
        Method to add an error log entry.
        """
        self.create_log_entry(
            action=action,
            status=RemoteLog.STATUS_FAILED,
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
        from .logs import RemoteLog
        """
        Method to create a log entry.
        """
        RemoteLog.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            content_object=self,
            sales_channel=self.sales_channel,
            action=action,
            status=status,
            response=response,
            payload=payload,
            error_traceback=error_traceback,
            identifier=identifier,
            user_error=user_error,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
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